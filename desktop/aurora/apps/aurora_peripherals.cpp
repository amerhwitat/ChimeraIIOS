#include <algorithm>
#include <filesystem>
#include <iostream>
#include <string>
#include <vector>
namespace fs=std::filesystem;
struct Device{std::string id,kind,path,backend;};
static std::vector<Device> discover(){
 std::vector<Device> out;
 auto add=[&](const std::string& p,const std::string& k,const std::string& b){
  std::error_code ec;
  for(const auto& e:fs::directory_iterator("/dev",ec)){if(ec)break;auto n=e.path().filename().string();if(n.rfind(p,0)==0)out.push_back({k+":"+n,k,e.path().string(),b});}
 };
 add("video","camera","PipeWire/V4L2/libcamera"); add("audio","audio","PipeWire/ALSA");
 add("event","input","evdev"); add("hidraw","hid","hidraw"); add("ttyUSB","serial","USB-serial");
 add("ttyACM","serial","USB-CDC"); add("spidev","spi","SPI"); add("i2c-","i2c","I2C");
 add("dri","gpu","DRM"); add("snd","audio","ALSA/PipeWire");
 std::sort(out.begin(),out.end(),[](auto&a,auto&b){return a.id<b.id;});
 out.erase(std::unique(out.begin(),out.end(),[](auto&a,auto&b){return a.id==b.id;}),out.end());
 return out;
}
static void help(){std::cout<<"Aurora Peripheral Center\nlist\nrequest <device-id>\ncamera <camera-device-id>\n";}
int main(int argc,char**argv){
 auto ds=discover(); std::string cmd=argc>1?argv[1]:"list";
 if(cmd=="--help"){help();return 0;}
 if(cmd=="list"){for(auto&d:ds)std::cout<<d.id<<" | "<<d.kind<<" | "<<d.path<<" | "<<d.backend<<"\n";return 0;}
 if((cmd=="request"||cmd=="camera")&&argc>2){
  auto it=std::find_if(ds.begin(),ds.end(),[&](auto&d){return d.id==argv[2];});
  if(it==ds.end()){std::cerr<<"Device not discovered\n";return 3;}
  if(cmd=="camera"&&it->kind!="camera"){std::cerr<<"Not a camera\n";return 4;}
  std::cout<<"Aurora permission request: "<<it->id<<"\nBackend: "<<it->backend<<"\nPath: "<<it->path<<"\nPolicy: explicit user request; Koronos/Aegis remains final authority.\n";return 0;
 }
 help(); return 2;
}