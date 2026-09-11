#pragma once
#include <string>
#include <vector>
#include <cmath>
struct WebRecord{std::string url,text;int status;};class WebLearningEngine{public:std::vector<WebRecord> crawl(const std::string&,int=10,int=1);double rnnScore(const std::vector<double>&s)const{double h=0,w=0;for(double x:s){h=std::tanh(x*.1+h*.05);w+=h*.01;}return 1/(1+std::exp(-w));}};
