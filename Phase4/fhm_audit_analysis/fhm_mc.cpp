// Conditional fixed-lot, two-phase target/loss simulation. Not broker execution.
#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <random>
#include <sstream>
#include <string>
#include <vector>
struct Trade { double gross, lower, upper; };
struct Result {
  int pass=0, overall=0, daily=0, unfinished=0, phase1=0;
  std::vector<int> days;
};
double quantile(std::vector<int> v, double q) {
  if(v.empty()) return -1;
  std::sort(v.begin(),v.end());
  double p=q*(v.size()-1); size_t a=static_cast<size_t>(p),b=std::min(a+1,v.size()-1);
  return v[a]+(v[b]-v[a])*(p-a);
}
int main(int argc,char**argv){
  if(argc!=3) return 2;
  std::ifstream f(argv[1]); std::ofstream out(argv[2]);
  if(!f || !out) return 3;
  out<<"id,n,pass,overall_breach,daily_breach,unfinished,phase1_pass,p_pass,mc_se,p10_days,median_days,p90_days\n";
  std::string id,file; double cost,lot,dd; int block,horizon,n,upper; unsigned long long seed;
  std::map<std::string,std::vector<Trade>> cache;
  while(f>>id>>file>>cost>>lot>>dd>>block>>horizon>>n>>seed>>upper){
    if(!cache.count(file)){
      std::ifstream tf(file); Trade t; std::vector<Trade> ts;
      while(tf>>t.gross>>t.lower>>t.upper) ts.push_back(t);
      if(ts.empty()) { std::cerr<<"Empty pool "<<file; return 4; }
      cache[file]=std::move(ts);
    }
    const auto &pool=cache[file];
    std::mt19937_64 rng(seed);
    std::uniform_int_distribution<size_t> pick(0,pool.size()-1);
    Result r;
    for(int path=0;path<n;++path){
      double pnl=0; int phase=0,phase_days=0,remaining=0; size_t index=0; bool done=false;
      for(int day=1;day<=horizon;++day){
        if(remaining==0){ index=pick(rng); remaining=block; }
        const Trade &t=pool[index];
        index=(index+1)%pool.size(); --remaining; ++phase_days;
        // $10 per index point per lot. Full scenario cost is charged up-front
        // for the equity test (conservative timing convention, not measured).
        double scale=10*lot;
        double adverse=upper?t.upper:t.lower;
        double loss=(adverse+cost)*scale;
        bool daily=(loss>=200-1e-10);
        bool overall=(pnl-loss<=-5000*dd+1e-10);
        if(daily||overall){
          if(daily) ++r.daily; else ++r.overall;
          done=true; break;
        }
        pnl+=(t.gross-cost)*scale;
        if(pnl<=-5000*dd+1e-10){++r.overall;done=true;break;}
        double target=phase==0?400:200;
        if(pnl>=target-1e-10 && phase_days>=2){
          if(phase==0){++r.phase1;phase=1;pnl=0;phase_days=0;}
          else {++r.pass;r.days.push_back(day);done=true;break;}
        }
      }
      if(!done) ++r.unfinished;
    }
    double p=double(r.pass)/n;
    out<<std::setprecision(12)<<id<<","<<n<<","<<r.pass<<","<<r.overall<<","<<r.daily<<","<<r.unfinished<<","<<r.phase1<<","<<p<<","<<std::sqrt(p*(1-p)/n)<<","<<quantile(r.days,.1)<<","<<quantile(r.days,.5)<<","<<quantile(r.days,.9)<<"\n";
  }
}