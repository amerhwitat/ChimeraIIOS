#include "chm_neural.hpp"
#include <algorithm>
#include <cctype>
#include <iostream>
#include <string>
#include <vector>
namespace {
std::string lower(std::string s){std::transform(s.begin(),s.end(),s.begin(),[](unsigned char c){return static_cast<char>(std::tolower(c));});return s;}
std::string respond(const std::string& input){
 const auto q=lower(input);
 if(q.empty()) return "Chimera Neural Network: please enter a message.";
 if(q=="help"||q.find("what can you do")!=std::string::npos) return "I am the Chimera neural chat surface. I can inspect questions, expose confidence, and route future inference to the trusted neural node fabric.";
 if(q.find("128d")!=std::string::npos) return "The experimental 128D profile can be used as a semantic feature space; it is not asserted to be a physical 128-dimensional space.";
 if(q.find("hello")!=std::string::npos||q.find("hi")!=std::string::npos) return "Hello. Chimera Neural Network is connected to Aurora.";
 return "Chimera Neural Network received: "+input;
}}
int main(){
 std::cout<<"Aurora - Chimera Neural Chat\nType /quit to close, /help for commands.\n\n";
 std::string line;
 while(std::cout<<"You > "&&std::getline(std::cin,line)){
  if(line=="/quit"||line=="/exit") break;
  if(line=="/confidence"){std::cout<<"Neural confidence uses weighted evidence disagreement.\n";continue;}
  std::vector<chm::neural::Evidence> evidence{{0.75,1.0},{0.65,0.8}};
  const auto r=chm::neural::reason(evidence);
  std::cout<<"Chimera > "<<respond(line)<<"\n";
  std::cout<<"           score="<<r.score<<" confidence="<<r.confidence<<"\n";
 }
 return 0;
}
