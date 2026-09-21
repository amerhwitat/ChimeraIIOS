#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
#include <cstdlib>
#include <chrono>
#include <ctime>
namespace fs=std::filesystem;
static void usage(){std::cout<<"chimera-utils: ls cat cp mv rm mkdir pwd echo touch head tail wc grep uname date whoami env\n";}
static int copy_file(const fs::path&a,const fs::path&b){fs::copy_file(a,b,fs::copy_options::overwrite_existing);return 0;}
int main(int argc,char**argv){
 if(argc<2){usage();return 2;} std::string c=argv[1];
 if(c=="pwd"){std::cout<<fs::current_path().string()<<"\n";return 0;}
 if(c=="whoami"){std::cout<<(std::getenv("USER")?std::getenv("USER"):"chimera")<<"\n";return 0;}
 if(c=="echo"){for(int i=2;i<argc;i++)std::cout<<(i>2?" ":"")<<argv[i];std::cout<<"\n";return 0;}
 if(c=="ls"){fs::path p=argc>2?argv[2]:".";for(auto&e:fs::directory_iterator(p))std::cout<<e.path().filename().string()<<"\n";return 0;}
 if(c=="cat"||c=="head"||c=="tail"){
   if(argc<3)return 2;std::ifstream f(argv[2]);if(!f)return 1;std::string line;std::vector<std::string> v;while(std::getline(f,line))v.push_back(line);
   size_t n=10;if(argc>3)n=std::stoul(argv[3]);size_t start=c=="tail"?(v.size()>n?v.size()-n:0):0,size=c=="head"?std::min(n,v.size()):v.size();for(size_t i=start;i<(c=="tail"?v.size():size);++i)std::cout<<v[i]<<"\n";return 0;
 }
 if(c=="wc"){if(argc<3)return 2;std::ifstream f(argv[2]);size_t lines=0,words=0,bytes=0;std::string s;while(std::getline(f,s)){lines++;bytes+=s.size()+1;std::istringstream x(s);std::string w;while(x>>w)words++;}std::cout<<lines<<" "<<words<<" "<<bytes<<" "<<argv[2]<<"\n";return 0;}
 if(c=="mkdir"){for(int i=2;i<argc;i++)fs::create_directories(argv[i]);return 0;}
 if(c=="touch"){for(int i=2;i<argc;i++){std::ofstream f(argv[i],std::ios::app);}return 0;}
 if(c=="cp"&&argc>=4)return copy_file(argv[2],argv[3]);
 if(c=="mv"&&argc>=4){fs::rename(argv[2],argv[3]);return 0;}
 if(c=="rm"){for(int i=2;i<argc;i++)fs::remove_all(argv[i]);return 0;}
 if(c=="uname"){std::cout<<"Chimera-II Koronos x86_64\n";return 0;}
 if(c=="date"){auto t=std::time(nullptr);std::cout<<std::ctime(&t);return 0;}
 if(c=="grep"&&argc>=4){std::ifstream f(argv[3]);std::string s;while(std::getline(f,s))if(s.find(argv[2])!=std::string::npos)std::cout<<s<<"\n";return 0;}
 if(c=="env"){for(char**e=environ;*e;++e)std::cout<<*e<<"\n";return 0;}
 usage();return 127;
}
