#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace {
struct Insn { std::uint8_t op{}; std::uint8_t width_log2{}; std::uint16_t rd{}; std::uint16_t rs1{}; std::uint16_t rs2{}; std::uint64_t imm{}; };
const char* name(std::uint8_t op){ static const char* n[]={"NOP","MOV","ADD","SUB","MUL","DIV","AND","OR","XOR","SHL","SHR","CMP","LOAD","STORE","CALL","RET","JMP","CJMP","TCONTRACT","MODEXP","NETSEND","SYSCALL","HALT"}; return op<sizeof(n)/sizeof(n[0])?n[op]:"UNKNOWN"; }
bool decode(const std::uint8_t* p,Insn& x){ x.op=p[0];x.width_log2=p[1];x.rd=p[2]|(p[3]<<8);x.rs1=p[4]|(p[5]<<8);x.rs2=p[6]|(p[7]<<8); for(int i=0;i<8;++i)x.imm|=(std::uint64_t)p[8+i]<<(i*8); return true; }
void disasm(const std::vector<std::uint8_t>& b){ if(b.size()%16) throw std::runtime_error("CHM instruction stream must be 16-byte aligned"); for(size_t pc=0;pc<b.size();pc+=16){Insn x;decode(&b[pc],x);std::cout<<std::hex<<std::setw(8)<<std::setfill('0')<<pc<<"  "<<name(x.op)<<"  r"<<std::dec<<x.rd<<",r"<<x.rs1<<",r"<<x.rs2<<"  width="<<(1u<<x.width_log2)<<"  imm=0x"<<std::hex<<x.imm<<"\n";}}
}
int main(int argc,char**argv){
 if(argc!=2){std::cerr<<"usage: chimera-dis <binary>\n";return 2;}
 std::ifstream f(argv[1],std::ios::binary); if(!f){std::cerr<<"cannot open "<<argv[1]<<"\n";return 1;}
 std::vector<std::uint8_t>b((std::istreambuf_iterator<char>(f)),{}); try{disasm(b);}catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;} return 0;
}
