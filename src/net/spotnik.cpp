#include <cstdint>
#include <iostream>
namespace spotnik {
enum class Owner:uint8_t{NIC,KERNEL,USER,RECYCLED};
struct PacketDesc{std::uint64_t buffer;std::uint32_t length;Owner owner;};
bool transfer(PacketDesc&p,Owner from,Owner to){if(p.owner!=from)return false;p.owner=to;return true;}
void demo(){PacketDesc p{0x100000,1500,Owner::NIC};transfer(p,Owner::NIC,Owner::KERNEL);transfer(p,Owner::KERNEL,Owner::USER);std::cout<<"[Spotnik] zero-copy ownership state="<<int(p.owner)<<"\n";}
}
