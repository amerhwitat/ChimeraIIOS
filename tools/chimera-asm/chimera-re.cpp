#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <vector>
int main(int argc,char**argv){
 if(argc!=2){std::cerr<<"usage: chimera-re <binary>\n";return 2;}
 std::ifstream f(argv[1],std::ios::binary); if(!f)return 1;
 std::vector<std::uint8_t>b((std::istreambuf_iterator<char>(f)),{});
 if(b.size()%16){std::cerr<<"not a CHIMERA-BIT canonical stream\n";return 1;}
 std::cout<<"CHIMERA-BIT reverse-engineering report\n";
 std::cout<<"bytes: "<<b.size()<<" instructions: "<<b.size()/16<<"\n";
 for(size_t pc=0;pc<b.size();pc+=16){
   auto op=b[pc]; std::cout<<std::hex<<std::setw(8)<<std::setfill('0')<<pc<<" op=0x"<<std::setw(2)<<(unsigned)op;
   std::cout<<" rd="<<std::dec<<(unsigned)(b[pc+2]|(b[pc+3]<<8));
   std::cout<<" rs1="<<(unsigned)(b[pc+4]|(b[pc+5]<<8));
   std::cout<<" rs2="<<(unsigned)(b[pc+6]|(b[pc+7]<<8))<<"\n";
 }
}
