#include "registry_store.hpp"
#include <cerrno>
#include <cstdio>
#include <cstring>
#include <algorithm>
#include <filesystem>
#include <fstream>
#include <tuple>
#include <sstream>
#include <utility>
#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <io.h>
#include <fcntl.h>
#include <sys/stat.h>
#ifndef O_CLOEXEC
#define O_CLOEXEC 0
#endif
#ifndef O_DIRECTORY
#define O_DIRECTORY 0
#endif
#ifndef O_CREAT
#define O_CREAT _O_CREAT
#endif
#ifndef O_TRUNC
#define O_TRUNC _O_TRUNC
#endif
#ifndef O_APPEND
#define O_APPEND _O_APPEND
#endif
#ifndef O_RDWR
#define O_RDWR _O_RDWR
#endif
#ifndef O_WRONLY
#define O_WRONLY _O_WRONLY
#endif
#ifndef O_RDONLY
#define O_RDONLY _O_RDONLY
#endif
#else
#include <fcntl.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <unistd.h>
#endif
namespace fs=std::filesystem;
namespace chimera::hive {
namespace {
std::string enc(const std::string&s){static const char h[]="0123456789abcdef";std::string o;o.reserve(s.size()*2);for(unsigned char c:s){o+=h[c>>4];o+=h[c&15];}return o;}
bool dec(const std::string&s,std::string&o){if(s.size()%2) return false;
 o.clear();auto n=[](char c){if(c>='0'&&c<='9')return c-'0';if(c>='a'&&c<='f')return c-'a'+10;if(c>='A'&&c<='F')return c-'A'+10;return -1;};for(size_t i=0;i<s.size();i+=2){int a=n(s[i]),b=n(s[i+1]);if(a<0||b<0)return false;o.push_back(char((a<<4)|b));}return true;}
long long write_fd(int fd,const void* data,size_t size){
#ifdef _WIN32
 return static_cast<long long>(::_write(fd,data,static_cast<unsigned int>(std::min<size_t>(size,0x7fffffff))));
#else
 return static_cast<long long>(::write(fd,data,size));
#endif
}
bool sync_fd(int fd){
#ifdef _WIN32
 return ::_commit(fd)==0;
#else
 return ::fsync(fd)==0;
#endif
}
int close_fd(int fd){
#ifdef _WIN32
 return ::_close(fd);
#else
 return ::close(fd);
#endif
}
int open_file(const std::string& path,int flags,int mode=0600){
#ifdef _WIN32
 int f=0;
 if(flags&O_CREAT) f|=_O_CREAT;
 if(flags&O_TRUNC) f|=_O_TRUNC;
 if(flags&O_APPEND) f|=_O_APPEND;
 if(flags&O_RDWR) f|=_O_RDWR;
 else if(flags&O_WRONLY) f|=_O_WRONLY;
 else f|=_O_RDONLY;
 f|=_O_BINARY;
 return ::_wopen(fs::path(path).c_str(),f,mode);
#else
 return ::open(path.c_str(),flags,mode);
#endif
}
void remove_file(const std::string& path){
#ifdef _WIN32
 ::_wunlink(fs::path(path).c_str());
#else
 ::unlink(path.c_str());
#endif
}
bool replace_file(const std::string& from,const std::string& to){
#ifdef _WIN32
 return ::MoveFileExW(fs::path(from).c_str(),fs::path(to).c_str(),MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH)!=0;
#else
 return ::rename(from.c_str(),to.c_str())==0;
#endif
}
bool writeall(int fd,const std::string&s){size_t p=0;while(p<s.size()){long long n=write_fd(fd,s.data()+p,s.size()-p);if(n<0&&errno==EINTR)continue;if(n<=0)return false;p+=static_cast<size_t>(n);}return true;}
bool valid_key(const std::string&k){if(k.empty()||k.front()=='/'||k.back()=='/'||k.size()>4096||k.find(char(0))!=std::string::npos)return false;size_t p=0;while(p<k.size()){size_t q=k.find('/',p);if(q==std::string::npos)q=k.size();if(q==p)return false;std::string part=k.substr(p,q-p);if(part=="."||part=="..")return false;p=q+1;}return true;}
struct Lock{
 bool locked{false};
#ifdef _WIN32
 HANDLE handle{INVALID_HANDLE_VALUE}; OVERLAPPED overlapped{};
 explicit Lock(const std::string&p){
  handle=::CreateFileW(fs::path(p).c_str(),GENERIC_READ|GENERIC_WRITE,FILE_SHARE_READ|FILE_SHARE_WRITE,nullptr,OPEN_ALWAYS,FILE_ATTRIBUTE_NORMAL,nullptr);
  if(handle!=INVALID_HANDLE_VALUE) locked=::LockFileEx(handle,LOCKFILE_EXCLUSIVE_LOCK,0,MAXDWORD,MAXDWORD,&overlapped)!=0;
  if(!locked&&handle!=INVALID_HANDLE_VALUE){::CloseHandle(handle);handle=INVALID_HANDLE_VALUE;}
 }
 ~Lock(){if(handle!=INVALID_HANDLE_VALUE){if(locked)::UnlockFileEx(handle,0,MAXDWORD,MAXDWORD,&overlapped);::CloseHandle(handle);}}
#else
 int fd{-1};
 explicit Lock(const std::string&p){fd=open_file(p,O_CREAT|O_RDWR|O_CLOEXEC,0600);if(fd>=0&&::flock(fd,LOCK_EX)==0)locked=true;else if(fd>=0){close_fd(fd);fd=-1;}}
 ~Lock(){if(fd>=0){if(locked)::flock(fd,LOCK_UN);close_fd(fd);}}
#endif
};
}
RegistryStore::RegistryStore(std::string d):directory_(std::move(d)){}
bool RegistryStore::open(){std::lock_guard<std::mutex>g(mutex_);std::error_code ec;fs::create_directories(directory_,ec);if(ec){error_=ec.message();return false;}
#ifndef _WIN32
 ::chmod(directory_.c_str(),0700);
#endif
 Lock l(directory_+"/registry.lock");if(!l.locked){error_="cannot lock registry";return false;}return recover_locked();}
bool RegistryStore::recover_locked(){
 values_.clear();sequence_=0;std::string line;const std::string snapshot_path=directory_+"/registry.db";std::ifstream sf(snapshot_path);
 if(!sf&&fs::exists(snapshot_path)){error_="cannot read registry snapshot";return false;}
 if(sf){if(!std::getline(sf,line)){error_="empty registry snapshot";return false;}if(line.rfind("CHMREG1|",0)!=0){error_="invalid snapshot header";return false;}try{size_t used=0;sequence_=std::stoull(line.substr(8),&used);if(used!=line.size()-8){error_="invalid snapshot sequence";return false;}}catch(...){error_="invalid snapshot sequence";return false;}while(std::getline(sf,line)){if(line.empty())continue;auto p=line.find('|');if(p==std::string::npos){error_="malformed registry snapshot row";return false;}std::string k,v;if(!dec(line.substr(0,p),k)||!valid_key(k)||!dec(line.substr(p+1),v)){error_="invalid registry snapshot row";return false;}values_[k]=v;}}
 const std::string wal_path=directory_+"/registry.wal";std::ifstream jf(wal_path);if(!jf&&fs::exists(wal_path)){error_="cannot read registry WAL";return false;}
 std::map<unsigned long long,std::vector<std::tuple<char,std::string,std::string>>> pending;std::vector<unsigned long long> committed;unsigned long long max_seen=sequence_;
 while(std::getline(jf,line)){std::istringstream in(line);char kind=0;unsigned long long tx=0;in>>kind>>tx;if(!in)continue;max_seen=std::max(max_seen,tx);
 if(kind=='S'){std::string kh,vh,k,v;in>>kh;if(in){std::getline(in,vh);if(!vh.empty()&&vh.front()==' ')vh.erase(0,1);if(vh.empty()||vh=="-")v.clear();else if(!dec(vh,v))continue;if(dec(kh,k)&&valid_key(k))pending[tx].push_back({'S',k,v});}}
 else if(kind=='D'){std::string kh,k;in>>kh;if(in&&dec(kh,k)&&valid_key(k))pending[tx].push_back({'D',k,std::string()});}
 else if(kind=='C')committed.push_back(tx);}
 for(auto tx:committed){if(tx<=sequence_)continue;auto it=pending.find(tx);if(it==pending.end())continue;for(auto&e:it->second){if(std::get<0>(e)=='D')values_.erase(std::get<1>(e));else values_[std::get<1>(e)]=std::get<2>(e);}if(tx>sequence_)sequence_=tx;}sequence_=std::max(sequence_,max_seen);return true;
}
bool RegistryStore::get(const std::string&k,std::string&v)const{std::lock_guard<std::mutex>g(mutex_);auto i=values_.find(k);if(i==values_.end())return false;v=i->second;return true;}
std::vector<std::pair<std::string,std::string>> RegistryStore::entries()const{std::lock_guard<std::mutex>g(mutex_);return {values_.begin(),values_.end()};}
bool RegistryStore::append_locked(const std::string&r){int fd=open_file(directory_+"/registry.wal",O_CREAT|O_WRONLY|O_APPEND|O_CLOEXEC,0600);if(fd<0){error_=std::strerror(errno);return false;}bool ok=writeall(fd,r)&&sync_fd(fd);int e=errno;close_fd(fd);if(!ok)error_=std::strerror(e);return ok;}
bool RegistryStore::set(const std::string&k,const std::string&v){return set_many({{k,v}});}
bool RegistryStore::set_many(const std::vector<std::pair<std::string,std::string>>&items){
 if(items.empty()) return true;
 for(const auto&e:items) {
  if(!valid_key(e.first)||e.second.size()>1048576) { error_="invalid key/value length"; return false; }
 }
 std::lock_guard<std::mutex>g(mutex_);Lock l(directory_+"/registry.lock");if(!l.locked){error_="cannot lock registry";return false;}if(!recover_locked())return false;
 auto prefix=[](const std::string&a,const std::string&b){return b.size()>a.size()&&b.compare(0,a.size(),a)==0&&b[a.size()]=='/';};
 for(size_t i=0;i<items.size();++i){
  for(const auto&old:values_)if(old.first!=items[i].first&&(prefix(old.first,items[i].first)||prefix(items[i].first,old.first))){error_="registry key conflicts with a VFS directory path";return false;}
  for(size_t j=0;j<items.size();++j)if(i!=j&&items[i].first!=items[j].first&&(prefix(items[i].first,items[j].first)||prefix(items[j].first,items[i].first))){error_="transaction contains a file/directory key conflict";return false;}
 }
 auto tx=sequence_+1;std::string record;
 for(const auto&e:items)record+="S "+std::to_string(tx)+" "+enc(e.first)+" "+(e.second.empty()?"-":enc(e.second))+"\n";
 record+="C "+std::to_string(tx)+"\n";if(!append_locked(record))return false;for(const auto&e:items)values_[e.first]=e.second;sequence_=tx;return true;
}
bool RegistryStore::erase(const std::string&k){if(!valid_key(k)){error_="invalid registry key";return false;}std::lock_guard<std::mutex>g(mutex_);Lock l(directory_+"/registry.lock");if(!l.locked){error_="cannot lock registry";return false;}if(!recover_locked())return false;auto tx=sequence_+1;if(!append_locked("D "+std::to_string(tx)+" "+enc(k)+"\nC "+std::to_string(tx)+"\n"))return false;values_.erase(k);sequence_=tx;return true;}
bool RegistryStore::write_snapshot_locked(){std::string tmp=directory_+"/registry.db.tmp",data="CHMREG1|"+std::to_string(sequence_)+"\n";for(auto&e:values_)data+=enc(e.first)+"|"+enc(e.second)+"\n";int fd=open_file(tmp,O_CREAT|O_TRUNC|O_WRONLY|O_CLOEXEC,0600);if(fd<0){error_=std::strerror(errno);return false;}bool ok=writeall(fd,data)&&sync_fd(fd);int e=errno;close_fd(fd);if(!ok||!replace_file(tmp,directory_+"/registry.db")){error_=std::strerror(e?e:errno);remove_file(tmp);return false;}
#ifndef _WIN32
 int d=::open(directory_.c_str(),O_RDONLY|O_DIRECTORY|O_CLOEXEC);if(d>=0){::fsync(d);::close(d);}
#endif
 return true;}
bool RegistryStore::compact(){std::lock_guard<std::mutex>g(mutex_);Lock l(directory_+"/registry.lock");if(!l.locked){error_="cannot lock registry";return false;}if(!recover_locked()||!write_snapshot_locked())return false;int fd=open_file(directory_+"/registry.wal",O_CREAT|O_TRUNC|O_WRONLY|O_CLOEXEC,0600);if(fd<0){error_=std::strerror(errno);return false;}bool ok=sync_fd(fd);close_fd(fd);if(!ok)error_="cannot sync WAL checkpoint";return ok;}
}