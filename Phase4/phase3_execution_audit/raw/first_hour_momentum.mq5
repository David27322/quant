#property copyright "David / First-Hour Momentum"
#property version   "1.00"
#property strict

#include <Trade/Trade.mqh>

/*
  First-Hour Momentum EA — FundedNext demo validation

  Locked strategy (New York time):
    09:30 M1 open = RTH open
    10:30 M1 open = signal price
    Direction      = sign(10:30 open - 09:30 open)
    Entry          = market on first tick of 10:31 M1 bar
    Stop/target    = 40 / 80 index points from ACTUAL fill
    Exit           = stop, target, or force-flat at 15:55 ET
    Frequency      = max one entry per New York trading day

  Attach to the FundedNext NDX100 chart. The EA always reads PERIOD_M1,
  regardless of chart timeframe. Default size is the smallest validated lot: 0.02.
*/

input double InpLots                    = 0.02;
input double InpStopPoints              = 40.0;
input double InpTargetR                 = 2.0;
input ulong  InpMagic                   = 26071031;
input double InpMaxEntryDeviationPoints = 2.0;   // log warning; not MT5 _Point units
input double InpExpectedPointValue      = 10.0;  // USD/index point/1.0 lot
input bool   InpAbortOnSpecMismatch     = true;
input bool   InpEnableTrading           = true;  // false = signal/log only
input string InpLogFile                 = "fhm_demo_fills.csv";

CTrade trade;
datetime g_last_m1_bar = 0;
int      g_ny_date_key = 0;
bool     g_traded_today = false;
bool     g_entry_pending = false;
double   g_expected_entry = 0.0;
double   g_actual_entry = 0.0;
double   g_stop_price = 0.0;
double   g_target_price = 0.0;
double   g_expected_exit = 0.0;
int      g_direction = 0; // +1 long, -1 short
ulong    g_position_id = 0;

string KeyPrefix()
{
   return "FHM." + _Symbol + "." + IntegerToString((long)InpMagic) + ".";
}

string GV(const string suffix) { return KeyPrefix() + suffix; }

int DateKey(const MqlDateTime &x)
{
   return x.year * 10000 + x.mon * 100 + x.day;
}

int FirstSunday(const int year, const int month)
{
   MqlDateTime x = {};
   x.year = year; x.mon = month; x.day = 1;
   datetime t = StructToTime(x);
   TimeToStruct(t, x);
   return 1 + ((7 - x.day_of_week) % 7);
}

int EasternUtcOffsetHours(const datetime utc)
{
   MqlDateTime u;
   TimeToStruct(utc, u);

   const int second_sunday_march = FirstSunday(u.year, 3) + 7;
   const int first_sunday_nov    = FirstSunday(u.year, 11);

   MqlDateTime a = {}, b = {};
   a.year = u.year; a.mon = 3;  a.day = second_sunday_march; a.hour = 7; // 02:00 EST
   b.year = u.year; b.mon = 11; b.day = first_sunday_nov;    b.hour = 6; // 02:00 EDT
   datetime dst_start_utc = StructToTime(a);
   datetime dst_end_utc   = StructToTime(b);
   return (utc >= dst_start_utc && utc < dst_end_utc) ? -4 : -5;
}

void GetNewYorkNow(MqlDateTime &ny)
{
   datetime utc = TimeGMT();
   TimeToStruct(utc + EasternUtcOffsetHours(utc) * 3600, ny);
}

int ServerUtcOffsetSeconds()
{
   // Live use only. Round to the nearest minute to remove call-time jitter.
   return (int)(MathRound((double)(TimeTradeServer() - TimeGMT()) / 60.0) * 60.0);
}

datetime NewYorkLocalToServer(const int year, const int mon, const int day,
                              const int hour, const int minute)
{
   // US markets are closed during the Sunday DST switch. A noon-UTC probe
   // therefore gives the correct offset for every trading timestamp used here.
   MqlDateTime local = {};
   local.year = year; local.mon = mon; local.day = day;
   local.hour = hour; local.min = minute;
   datetime nominal_local = StructToTime(local);
   datetime probe_utc = nominal_local + 5 * 3600;
   int eastern_offset = EasternUtcOffsetHours(probe_utc);
   datetime utc = nominal_local - eastern_offset * 3600;
   return utc + ServerUtcOffsetSeconds();
}

bool ExactM1Open(const MqlDateTime &ny_day, const int hour, const int minute,
                 double &price)
{
   datetime server_time = NewYorkLocalToServer(ny_day.year, ny_day.mon, ny_day.day,
                                                hour, minute);
   int shift = iBarShift(_Symbol, PERIOD_M1, server_time, true);
   if(shift < 0)
      return false;
   datetime found = iTime(_Symbol, PERIOD_M1, shift);
   if(found != server_time)
      return false;
   price = iOpen(_Symbol, PERIOD_M1, shift);
   return (price > 0.0);
}

double NormalizePrice(const double price)
{
   double tick = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tick <= 0.0) tick = _Point;
   return NormalizeDouble(MathRound(price / tick) * tick, _Digits);
}

double NormalizeVolume(const double requested)
{
   double vmin = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double vmax = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   if(step <= 0.0) return 0.0;
   double v = MathRound(requested / step) * step;
   v = MathMax(vmin, MathMin(vmax, v));
   return NormalizeDouble(v, 8);
}

bool ValidateSymbolSpec()
{
   double tick_size  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double tick_value = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double point_value = (tick_size > 0.0 ? tick_value / tick_size : 0.0);
   double volume = NormalizeVolume(InpLots);

   PrintFormat("FHM spec | symbol=%s digits=%d tick_size=%.8f tick_value=%.8f "
               "point_value=%.4f lot_requested=%.4f lot_normalized=%.4f",
               _Symbol, _Digits, tick_size, tick_value, point_value,
               InpLots, volume);

   bool ok = true;
   if(volume <= 0.0 || MathAbs(volume - InpLots) > 1e-8)
   {
      Print("FHM ERROR: requested lot is invalid for this symbol's min/max/step.");
      ok = false;
   }
   double tolerance = MathMax(0.01, InpExpectedPointValue * 0.02);
   if(point_value <= 0.0 || MathAbs(point_value - InpExpectedPointValue) > tolerance)
   {
      PrintFormat("FHM ERROR: point value %.4f differs from expected %.4f USD/point/lot.",
                  point_value, InpExpectedPointValue);
      ok = false;
   }
   long trade_mode = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_MODE);
   if(trade_mode == SYMBOL_TRADE_MODE_DISABLED)
   {
      Print("FHM ERROR: trading is disabled for this symbol.");
      ok = false;
   }
   return ok;
}

bool FindOurPosition(ulong &ticket)
{
   for(int i = PositionsTotal() - 1; i >= 0; --i)
   {
      ulong t = PositionGetTicket(i);
      if(t == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      if((ulong)PositionGetInteger(POSITION_MAGIC) != InpMagic) continue;
      ticket = t;
      return true;
   }
   ticket = 0;
   return false;
}

bool TradedOnNyDate(const MqlDateTime &ny)
{
   datetime from_server = NewYorkLocalToServer(ny.year, ny.mon, ny.day, 0, 0);
   if(!HistorySelect(from_server, TimeTradeServer() + 60))
      return false;
   for(int i = HistoryDealsTotal() - 1; i >= 0; --i)
   {
      ulong deal = HistoryDealGetTicket(i);
      if(deal == 0) continue;
      if(HistoryDealGetString(deal, DEAL_SYMBOL) != _Symbol) continue;
      if((ulong)HistoryDealGetInteger(deal, DEAL_MAGIC) != InpMagic) continue;
      long entry = HistoryDealGetInteger(deal, DEAL_ENTRY);
      if(entry == DEAL_ENTRY_IN || entry == DEAL_ENTRY_INOUT)
         return true;
   }
   return false;
}

void SaveState()
{
   GlobalVariableSet(GV("expected_entry"), g_expected_entry);
   GlobalVariableSet(GV("actual_entry"), g_actual_entry);
   GlobalVariableSet(GV("stop"), g_stop_price);
   GlobalVariableSet(GV("target"), g_target_price);
   GlobalVariableSet(GV("direction"), (double)g_direction);
   GlobalVariableSet(GV("position_id"), (double)g_position_id);
   GlobalVariableSet(GV("date_key"), (double)g_ny_date_key);
}

void LoadState()
{
   if(GlobalVariableCheck(GV("expected_entry"))) g_expected_entry = GlobalVariableGet(GV("expected_entry"));
   if(GlobalVariableCheck(GV("actual_entry")))   g_actual_entry   = GlobalVariableGet(GV("actual_entry"));
   if(GlobalVariableCheck(GV("stop")))           g_stop_price     = GlobalVariableGet(GV("stop"));
   if(GlobalVariableCheck(GV("target")))         g_target_price   = GlobalVariableGet(GV("target"));
   if(GlobalVariableCheck(GV("direction")))      g_direction      = (int)GlobalVariableGet(GV("direction"));
   if(GlobalVariableCheck(GV("position_id")))    g_position_id    = (ulong)GlobalVariableGet(GV("position_id"));
}

void WriteLog(const string event_name, const ulong position_id,
              const int direction, const double expected_price,
              const double actual_price, const double adverse_points,
              const string reason)
{
   int h = FileOpen(InpLogFile,
                    FILE_READ|FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_SHARE_READ,
                    ',');
   if(h == INVALID_HANDLE)
   {
      PrintFormat("FHM ERROR: cannot open log %s, error=%d", InpLogFile, GetLastError());
      return;
   }
   if(FileSize(h) == 0)
      FileWrite(h, "event", "ny_date", "position_id", "symbol", "direction",
                "expected_price", "actual_price", "adverse_points", "reason",
                "server_time");
   FileSeek(h, 0, SEEK_END);
   MqlDateTime ny;
   GetNewYorkNow(ny);
   string ds = StringFormat("%04d-%02d-%02d", ny.year, ny.mon, ny.day);
   string side = (direction > 0 ? "LONG" : (direction < 0 ? "SHORT" : "UNKNOWN"));
   FileWrite(h, event_name, ds, IntegerToString((long)position_id), _Symbol, side,
             DoubleToString(expected_price, _Digits),
             DoubleToString(actual_price, _Digits),
             DoubleToString(adverse_points, 4), reason,
             TimeToString(TimeTradeServer(), TIME_DATE|TIME_SECONDS));
   FileFlush(h);
   FileClose(h);
}

bool SetExactBracket(const ulong ticket, const double actual_fill)
{
   double target_points = InpStopPoints * InpTargetR;
   if(g_direction > 0)
   {
      g_stop_price   = NormalizePrice(actual_fill - InpStopPoints);
      g_target_price = NormalizePrice(actual_fill + target_points);
   }
   else
   {
      g_stop_price   = NormalizePrice(actual_fill + InpStopPoints);
      g_target_price = NormalizePrice(actual_fill - target_points);
   }
   if(!trade.PositionModify(ticket, g_stop_price, g_target_price))
   {
      PrintFormat("FHM CRITICAL: bracket modify failed retcode=%u %s",
                  trade.ResultRetcode(), trade.ResultRetcodeDescription());
      return false;
   }
   SaveState();
   return true;
}

void EnterAt1031(const MqlDateTime &ny)
{
   if(g_traded_today || g_entry_pending)
      return;

   double rth_open = 0.0, signal_open = 0.0, entry_open = 0.0;
   if(!ExactM1Open(ny, 9, 30, rth_open) ||
      !ExactM1Open(ny, 10, 30, signal_open) ||
      !ExactM1Open(ny, 10, 31, entry_open))
   {
      Print("FHM SKIP: exact 09:30/10:30/10:31 M1 bars are not available.");
      return;
   }
   if(signal_open == rth_open)
   {
      Print("FHM SKIP: first-hour move is exactly zero.");
      g_traded_today = true; // deterministic no-trade day; avoid repeated attempts
      return;
   }

   g_direction = (signal_open > rth_open ? 1 : -1);
   g_expected_entry = entry_open;
   g_entry_pending = true;

   PrintFormat("FHM SIGNAL | NY=%04d-%02d-%02d side=%s 09:30=%.2f 10:30=%.2f expected_10:31=%.2f",
               ny.year, ny.mon, ny.day, (g_direction > 0 ? "LONG" : "SHORT"),
               rth_open, signal_open, g_expected_entry);

   if(!InpEnableTrading)
   {
      WriteLog("SIGNAL_ONLY", 0, g_direction, g_expected_entry, 0.0, 0.0, "trading_disabled");
      g_traded_today = true;
      g_entry_pending = false;
      return;
   }

   MqlTick q;
   if(!SymbolInfoTick(_Symbol, q))
   {
      Print("FHM ERROR: no live quote at entry.");
      g_entry_pending = false;
      return;
   }

   double volume = NormalizeVolume(InpLots);
   double provisional_fill = (g_direction > 0 ? q.ask : q.bid);
   double provisional_sl, provisional_tp;
   if(g_direction > 0)
   {
      provisional_sl = NormalizePrice(provisional_fill - InpStopPoints);
      provisional_tp = NormalizePrice(provisional_fill + InpStopPoints * InpTargetR);
   }
   else
   {
      provisional_sl = NormalizePrice(provisional_fill + InpStopPoints);
      provisional_tp = NormalizePrice(provisional_fill - InpStopPoints * InpTargetR);
   }

   bool sent = (g_direction > 0)
               ? trade.Buy(volume, _Symbol, 0.0, provisional_sl, provisional_tp, "FHM")
               : trade.Sell(volume, _Symbol, 0.0, provisional_sl, provisional_tp, "FHM");
   if(!sent)
   {
      PrintFormat("FHM ENTRY FAILED retcode=%u %s",
                  trade.ResultRetcode(), trade.ResultRetcodeDescription());
      g_entry_pending = false;
      return;
   }

   double actual = trade.ResultPrice();
   ulong ticket = 0;
   if(actual <= 0.0 || !FindOurPosition(ticket))
   {
      Print("FHM CRITICAL: order reported success but position/fill was not found.");
      g_entry_pending = false;
      return;
   }

   g_actual_entry = actual;
   g_position_id = (ulong)PositionGetInteger(POSITION_IDENTIFIER);
   double adverse = (g_direction > 0 ? actual - g_expected_entry
                                     : g_expected_entry - actual);
   WriteLog("ENTRY", g_position_id, g_direction, g_expected_entry,
            actual, adverse, (MathAbs(actual - g_expected_entry) > InpMaxEntryDeviationPoints
                              ? "DEVIATION_OVER_2PT" : "OK"));

   if(MathAbs(actual - g_expected_entry) > InpMaxEntryDeviationPoints)
      PrintFormat("FHM WARNING: entry deviation %.2f pts exceeds %.2f pts.",
                  MathAbs(actual - g_expected_entry), InpMaxEntryDeviationPoints);

   if(!SetExactBracket(ticket, actual))
   {
      // Never knowingly leave an unprotected position. Attempt immediate close.
      if(!trade.PositionClose(ticket))
         Print("FHM EMERGENCY: bracket failed AND emergency close failed. Close manually now.");
   }

   g_traded_today = true;
   g_entry_pending = false;
}

void ForceFlatAt1555()
{
   ulong ticket = 0;
   if(!FindOurPosition(ticket))
      return;

   MqlTick q;
   if(!SymbolInfoTick(_Symbol, q))
   {
      Print("FHM ERROR: no quote for 15:55 force-flat; retrying on next tick.");
      return;
   }
   g_expected_exit = (g_direction > 0 ? q.bid : q.ask);
   GlobalVariableSet(GV("expected_exit"), g_expected_exit);
   if(!trade.PositionClose(ticket))
      PrintFormat("FHM ERROR: 15:55 close failed retcode=%u %s; retrying on next tick.",
                  trade.ResultRetcode(), trade.ResultRetcodeDescription());
}

string DealReasonText(const long reason)
{
   if(reason == DEAL_REASON_SL)     return "SL";
   if(reason == DEAL_REASON_TP)     return "TP";
   if(reason == DEAL_REASON_EXPERT) return "EOD_EXPERT";
   if(reason == DEAL_REASON_CLIENT) return "CLIENT";
   if(reason == DEAL_REASON_MOBILE) return "MOBILE";
   if(reason == DEAL_REASON_WEB)    return "WEB";
   return IntegerToString(reason);
}

int OnInit()
{
   trade.SetExpertMagicNumber(InpMagic);
   trade.SetTypeFillingBySymbol(_Symbol);
   // CTrade deviation is in the symbol's _Point units, not index points.
   trade.SetDeviationInPoints((ulong)MathMax(1.0,
      MathRound(InpMaxEntryDeviationPoints / _Point)));

   if(!ValidateSymbolSpec() && InpAbortOnSpecMismatch)
      return INIT_FAILED;

   MqlDateTime ny;
   GetNewYorkNow(ny);
   g_ny_date_key = DateKey(ny);
   LoadState();
   g_traded_today = TradedOnNyDate(ny);
   g_last_m1_bar = iTime(_Symbol, PERIOD_M1, 0);

   PrintFormat("FHM READY | NY date=%d traded_today=%s lot=%.2f auto=%s log=%s",
               g_ny_date_key, (g_traded_today ? "true" : "false"), InpLots,
               (InpEnableTrading ? "true" : "false"), InpLogFile);
   EventSetTimer(1);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
}

void ProcessClock()
{
   MqlDateTime ny;
   GetNewYorkNow(ny);
   int key = DateKey(ny);
   if(key != g_ny_date_key)
   {
      g_ny_date_key = key;
      g_traded_today = TradedOnNyDate(ny);
      g_entry_pending = false;
   }

   datetime bar = iTime(_Symbol, PERIOD_M1, 0);
   bool new_bar = (bar > 0 && bar != g_last_m1_bar);
   if(new_bar) g_last_m1_bar = bar;

   // Enter only on the first tick/new-bar event of 10:31. If the EA is started
   // a few seconds late within that minute, allow one recovery attempt.
   if(ny.hour == 10 && ny.min == 31 && !g_traded_today && (new_bar || !g_entry_pending))
      EnterAt1031(ny);

   // Flat at the first available quote at/after 15:55, never carry overnight.
   if((ny.hour > 15 || (ny.hour == 15 && ny.min >= 55)))
      ForceFlatAt1555();
}

void OnTick()  { ProcessClock(); }
void OnTimer() { ProcessClock(); }

void OnTradeTransaction(const MqlTradeTransaction &trans,
                        const MqlTradeRequest &request,
                        const MqlTradeResult &result)
{
   if(trans.type != TRADE_TRANSACTION_DEAL_ADD || trans.deal == 0)
      return;
   if(!HistoryDealSelect(trans.deal))
      return;
   if(HistoryDealGetString(trans.deal, DEAL_SYMBOL) != _Symbol)
      return;
   if((ulong)HistoryDealGetInteger(trans.deal, DEAL_MAGIC) != InpMagic)
      return;

   long entry_kind = HistoryDealGetInteger(trans.deal, DEAL_ENTRY);
   if(entry_kind != DEAL_ENTRY_OUT && entry_kind != DEAL_ENTRY_OUT_BY &&
      entry_kind != DEAL_ENTRY_INOUT)
      return;

   double actual_exit = HistoryDealGetDouble(trans.deal, DEAL_PRICE);
   ulong pos_id = (ulong)HistoryDealGetInteger(trans.deal, DEAL_POSITION_ID);
   long reason_code = HistoryDealGetInteger(trans.deal, DEAL_REASON);
   string reason = DealReasonText(reason_code);

   double expected_exit = 0.0;
   if(reason_code == DEAL_REASON_SL)
      expected_exit = g_stop_price;
   else if(reason_code == DEAL_REASON_TP)
      expected_exit = g_target_price;
   else
   {
      if(GlobalVariableCheck(GV("expected_exit")))
         expected_exit = GlobalVariableGet(GV("expected_exit"));
      if(expected_exit <= 0.0)
         expected_exit = actual_exit;
   }

   double adverse_exit = (g_direction > 0 ? expected_exit - actual_exit
                                          : actual_exit - expected_exit);
   WriteLog("EXIT", pos_id, g_direction, expected_exit, actual_exit,
            adverse_exit, reason);
   PrintFormat("FHM EXIT | reason=%s expected=%.2f actual=%.2f adverse=%.2f pts",
               reason, expected_exit, actual_exit, adverse_exit);
}
