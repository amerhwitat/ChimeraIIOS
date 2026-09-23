#include <cstdint>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
static std::uint8_t opcode(const std::string&s){const char* n[]={"NOP","MOV","ADD","SUB","MUL","DIV","AND","OR","XOR","SHL","SHR","CMP","LOAD","STORE","CALL","RET","JMP","CJMP","TCONTRACT","MODEXP","NETSEND","SYSCALL","HALT"};for(std::uint8_t i=0;i<sizeof(n)/sizeof(n[0]);++i)if(s==n[i])return i;return 0xff;}
int main(int argc,char**argv){if(argc!=3){std::cerr<<"usage: chimera-as input.asm output.chm\n";return 2;}std::ifstream in(argv[1]);std::ofstream out(argv[2],std::ios::binary);if(!in||!out)return 1;std::string op;while(in>>op){if(op[0]=='#'){std::string x;std::getline(in,x);continue;}auto o=opcode(op);if(o==0xff){std::cerr<<"unknown opcode: "<<op<<"\n";return 1;}std::uint8_t b[16]{};b[0]=o;b[1]=13;out.write(reinterpret_cast<char*>(b),16);}return 0;}
