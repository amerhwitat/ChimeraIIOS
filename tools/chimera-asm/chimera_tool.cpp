#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <vector>
namespace {
struct Insn{std::uint8_t op{},width_log2{};std::uint16_t rd{},rs1{},rs2{};std::uint64_t imm{};};
const char* name(std::uint8_t op){static const char*n[]={"NOP","MOV","ADD","SUB","MUL","DIV","AND","OR","XOR","SHL","SHR","CMP","LOAD","STORE","CALL","RET","JMP","CJMP","TCONTRACT","MODEXP","NETSEND","SYSCALL","HALT"};return op<sizeof(n)/sizeof(n[0])?n[op]:"UNKNOWN";}
bool decode(const std::uint8_t*p,Insn&x){x.op=p[0];x.width_log2=p[1];x.rd=p[2]|(p[3]<<8);x.rs1=p[4]|(p[5]<<8);x.rs2=p[6]|(p[7]<<8);for(int i=0;i<8;++i)x.imm|=(std::uint64_t)p[8+i]<<(i*8);return true;}
}
int main(int argc,char**argv){
 if(argc!=2){std::cerr<<"usage: chimera-dis <binary>\n";return 2;}
 std::ifstream f(argv[1],std::ios::binary);if(!f)return 1;
 std::vector<std::uint8_t>b((std::istreambuf_iterator<char>(f)),{});
 if(b.size()%16){std::cerr<<"invalid CHIMERA-BIT stream: size is not 16-byte aligned\n";return 1;}
 std::cout<<"# CHIMERA-BIT RegisterN disassembly\n";
 for(size_t pc=0;pc<b.size();pc+=16){Insn x;decode(&b[pc],x);const unsigned long long width=1ULL<<x.width_log2;
  std::cout<<std::hex<<std::setw(8)<<std::setfill('0')<<pc<<"  "<<name(x.op)<<" r"<<std::dec<<x.rd<<", r"<<x.rs1<<", r"<<x.rs2<<" ; width="<<width<<" imm=0x"<<std::hex<<x.imm<<"\n";
 }
}
