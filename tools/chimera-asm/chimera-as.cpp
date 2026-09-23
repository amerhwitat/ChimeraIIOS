#include <cstdint>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
#include <algorithm>
static std::uint8_t opcode(const std::string&s){
 const char* n[]={"NOP","MOV","ADD","SUB","MUL","DIV","AND","OR","XOR","SHL","SHR","CMP","LOAD","STORE","CALL","RET","JMP","CJMP","TCONTRACT","MODEXP","NETSEND","SYSCALL","HALT"};
 for(std::uint8_t i=0;i<sizeof(n)/sizeof(n[0]);++i)if(s==n[i])return i;return 0xff;
}
static bool reg(const std::string&s,std::uint16_t& r){if(s.size()<2||s[0]!='r')return false;try{auto v=std::stoul(s.substr(1));if(v>65535)return false;r=(std::uint16_t)v;return true;}catch(...){return false;}}
int main(int argc,char**argv){
 if(argc!=3){std::cerr<<"usage: chimera-as input.asm output.chm\n";return 2;}
 std::ifstream in(argv[1]);std::ofstream out(argv[2],std::ios::binary);if(!in||!out)return 1;
 std::string line;
 while(std::getline(in,line)){
  auto hash=line.find('#');if(hash!=std::string::npos)line.resize(hash);
  std::istringstream ss(line);std::string op; if(!(ss>>op))continue;
  auto o=opcode(op);if(o==0xff){std::cerr<<"unknown opcode: "<<op<<"\n";return 1;}
  std::uint8_t b[16]{};b[0]=o;b[1]=13;std::string a;std::vector<std::string> args;
  while(ss>>a){if(a.back()==',')a.pop_back();args.push_back(a);}
  std::uint16_t r=0;
  if(!args.empty()&&!reg(args[0],r)){std::cerr<<"bad register: "<<args[0]<<"\n";return 1;}b[2]=r&255;b[3]=r>>8;
  if(args.size()>1&&!reg(args[1],r)){std::cerr<<"bad register: "<<args[1]<<"\n";return 1;}if(args.size()>1){b[4]=r&255;b[5]=r>>8;}
  if(args.size()>2&&!reg(args[2],r)){std::cerr<<"bad register: "<<args[2]<<"\n";return 1;}if(args.size()>2){b[6]=r&255;b[7]=r>>8;}
  out.write(reinterpret_cast<char*>(b),16);
 }
 return 0;
}
