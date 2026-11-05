#define FUSE_USE_VERSION 31
#include "registry_store.hpp"
#include <fuse.h>
#include <cerrno>
#include <algorithm>
#include <cstdio>
#include <fcntl.h>
#include <cstring>
#include <string>
#include <sys/stat.h>
#include <unistd.h>
static chimera::hive::RegistryStore* db=nullptr;
static bool is_dir(const std::string&p){if(p=="/")return true;auto all=db->entries();std::string prefix=p.substr(1)+"/";for(auto&e:all)if(e.first.rfind(prefix,0)==0)return true;return false;}
static int attr(const char*p,struct stat*st,struct fuse_file_info*){memset(st,0,sizeof(*st));std::string path=p;if(path=="/"||is_dir(path)){st->st_mode=S_IFDIR|0755;st->st_nlink=2;return 0;}std::string value;if(!db->get(path.substr(1),value))return -ENOENT;st->st_mode=S_IFREG|0644;st->st_nlink=1;st->st_size=off_t(value.size());return 0;}
static int read_dir(const char*p,void*b,fuse_fill_dir_t fill,off_t,struct fuse_file_info*,enum fuse_readdir_flags){fill(b,".",nullptr,0,(enum fuse_fill_dir_flags)0);fill(b,"..",nullptr,0,(enum fuse_fill_dir_flags)0);std::string prefix=p;if(prefix=="/")prefix.clear();else{prefix.erase(0,1);prefix+="/";}for(auto&e:db->entries()){if(e.first.rfind(prefix,0)!=0)continue;std::string rest=e.first.substr(prefix.size());auto slash=rest.find('/');std::string child=rest.substr(0,slash);if(!child.empty())fill(b,child.c_str(),nullptr,0,(enum fuse_fill_dir_flags)0);}return 0;}
static int read_file(const char*p,char*b,size_t n,off_t off,struct fuse_file_info*){std::string v;if(!db->get(std::string(p).substr(1),v))return -ENOENT;if(off<0||size_t(off)>=v.size())return 0;size_t count=std::min(n,v.size()-size_t(off));memcpy(b,v.data()+off,count);return int(count);}
static int write_file(const char*p,const char*b,size_t n,off_t off,struct fuse_file_info*){std::string key=std::string(p).substr(1),v;db->get(key,v);if(off<0||size_t(off)>1024*1024||n>1024*1024-size_t(off))return -EFBIG;if(v.size()<size_t(off)+n)v.resize(size_t(off)+n,'\0');memcpy(v.data()+off,b,n);return db->set(key,v)?int(n):-EIO;}
static int create_file(const char*p,mode_t,struct fuse_file_info*){return db->set(std::string(p).substr(1),"")?0:-EIO;}
static int remove_file(const char*p){return db->erase(std::string(p).substr(1))?0:-EIO;}
static int make_dir(const char*,mode_t){return -EOPNOTSUPP;}
static int open_file(const char*p,struct fuse_file_info*fi){if(is_dir(p))return -EISDIR;std::string key=std::string(p).substr(1),v;if(!db->get(key,v)){if((fi->flags&O_CREAT)==0)return -ENOENT;if(!db->set(key,""))return -EIO;}if((fi->flags&O_TRUNC)!=0&&!db->set(key,""))return -EIO;return 0;}
int main(int argc,char**argv){if(argc<3){fprintf(stderr,"Usage: chm-registry-mount DATABASE_DIR MOUNTPOINT [FUSE options]\n");return 2;}std::string dir=argv[1];if(access(argv[2],F_OK)!=0&&mkdir(argv[2],0755)!=0){perror("mkdir");return 1;}chimera::hive::RegistryStore store(dir);if(!store.open()){fprintf(stderr,"registry open failed: %s\n",store.last_error().c_str());return 1;}db=&store;struct fuse_operations ops{};ops.getattr=attr;ops.readdir=read_dir;ops.read=read_file;ops.write=write_file;ops.create=create_file;ops.unlink=remove_file;ops.mkdir=make_dir;ops.open=open_file;char*args[argc];args[0]=argv[0];for(int i=2;i<argc;i++)args[i-1]=argv[i];args[argc-1]=nullptr;return fuse_main(argc-1,args,&ops,nullptr);}
