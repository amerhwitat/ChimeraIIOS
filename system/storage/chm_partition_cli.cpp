#include "chm_partition_cli.hpp"
#include "chimera_partition.hpp"
#include <iostream>
#include <sstream>
#include <string>
namespace chimera::storage {
static bool yes(int argc,char**argv){for(int i=1;i<argc;i++)if(std::string(argv[i])=="--yes-i-really-mean-it")return true;return false;}
static void usage(const std::string&m){std::cout<<m<<" TARGET [-l|--list] [--create START_LBA SECTORS] [--delete N] [--wipe] [--yes-i-really-mean-it]\\n";}
int partition_cli(const std::string&mode,int argc,char**argv){
 if(argc<2){usage(mode);return 2;}std::string path=argv[1];
 if(mode=="diskpart"){
  std::cout<<"Chimera II native DiskPart interpreter. Type help or exit.\\n";std::string line;
  while(std::cout<<"chm-diskpart> "&&std::getline(std::cin,line)){
   std::istringstream in(line);std::string a,b,c;in>>a>>b>>c;
   if(a=="exit"||a=="quit")break;
   if(a=="help"){std::cout<<"list disk | select disk TARGET | list partition | create partition primary size=MiB | delete partition N | clean\\n";continue;}
   if(a=="select"&&b=="disk"){path=c;std::cout<<"disk selected\\n";continue;}
   if(a=="list"){Disk d;std::string e;if(inspect(path,d,e)){std::string x;print_disk(d,x);std::cout<<x;}else std::cout<<e<<"\\n";continue;}
   if(a=="delete"&&b=="partition"){if(!yes(argc,argv)){std::cout<<"write requires --yes-i-really-mean-it\\n";continue;}std::string e;if(delete_partition(path,std::stoul(c),e))std::cout<<"partition deleted\\n";else std::cout<<e<<"\\n";continue;}
   if(a=="clean"){if(!yes(argc,argv)){std::cout<<"write requires --yes-i-really-mean-it\\n";continue;}std::string e;if(wipe_partition_table(path,e))std::cout<<"partition table cleared\\n";else std::cout<<e<<"\\n";continue;}
   if(a=="create"&&b=="partition"){if(!yes(argc,argv)){std::cout<<"write requires --yes-i-really-mean-it\\n";continue;}auto k=c.find("size=");uint64_t mib=k==std::string::npos?0:std::stoull(c.substr(k+5));Disk d;std::string e;if(!inspect(path,d,e)){std::cout<<e<<"\\n";continue;}uint64_t start=2048;if(!d.partitions.empty()){auto&q=d.partitions.back();start=q.start_lba+q.sectors+2048;}if(create_partition(path,d.label,start,mib*2048,0x83,"","",e))std::cout<<"partition created\\n";else std::cout<<e<<"\\n";continue;}
   std::cout<<"unknown command\\n";
  }return 0;
 }
 if(argc==2||std::string(argv[2])=="-l"||std::string(argv[2])=="--list"){Disk d;std::string e;if(!inspect(path,d,e)){std::cerr<<e<<"\\n";return 1;}std::string x;print_disk(d,x);std::cout<<x;return 0;}
 if(!yes(argc,argv)){std::cerr<<"write operation requires --yes-i-really-mean-it\\n";return 3;}
 std::string e,op=argv[2];
 if(op=="--wipe")return wipe_partition_table(path,e)?0:(std::cerr<<e<<"\\n",1);
 if(op=="--delete"&&argc>3)return delete_partition(path,std::stoul(argv[3]),e)?0:(std::cerr<<e<<"\\n",1);
 if(op=="--create"&&argc>4)return create_partition(path,"mbr",std::stoull(argv[3]),std::stoull(argv[4]),0x83,"","",e)?0:(std::cerr<<e<<"\\n",1);
 usage(mode);return 2;
}}