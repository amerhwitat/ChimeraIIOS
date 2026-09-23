#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <set>
#include <string>
#include <vector>
static const char* name(std::uint8_t op){static const char*n[]={"NOP","MOV","ADD","SUB","MUL","DIV","AND","OR","XOR","SHL","SHR","CMP","LOAD","STORE","CALL","RET","JMP","CJMP","TCONTRACT","MODEXP","NETSEND","SYSCALL","HALT"};return op<sizeof(n)/sizeof(n[0])?n[op]:"UNKNOWN";}
int main(int argc,char**argv){
 if(argc!=2){std::cerr<<"usage: chimera-re <binary>\n";return 2;}
 std::ifstream f(argv[1],std::ios::binary);if(!f)return 1;
 std::vector<std::uint8_t>b((std::istreambuf_iterator<char>(f)),{});
 if(b.size()%16){std::cerr<<"not a CHIMERA-BIT canonical stream\n";return 1;}
 std::set<unsigned>used;
 std::cout<<"CHIMERA-BIT reverse-engineering report\nbytes: "<<b.size()<<" instructions: "<<b.size()/16<<"\n\n";
 for(size_t pc=0;pc<b.size();pc+=16){
  const auto op=b[pc];const unsigned rd=b[pc+2]|(b[pc+3]<<8),r1=b[pc+4]|(b[pc+5]<<8),r2=b[pc+6]|(b[pc+7]<<8);
  used.insert(rd);used.insert(r1);used.insert(r2);
  std::cout<<std::hex<<std::setw(8)<<std::setfill('0')<<pc<<"  "<<name(op)<<" r"<<std::dec<<rd<<",r"<<r1<<",r"<<r2<<" width="<<(1ULL<<b[pc+1])<<"\n";
  if(op==14||op==16||op==17)std::cout<<"          control-flow target/candidate at imm=0x"<<std::hex<<*reinterpret_cast<const std::uint64_t*>(&b[pc+8])<<"\n";
 }
 std::cout<<"\nregisters referenced: "<<used.size()<<"\n";
 for(auto r:used)std::cout<<"r"<<r<<" ";
 std::cout<<"\n";
}
