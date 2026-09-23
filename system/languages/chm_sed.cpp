#include <fstream>
#include <iostream>
#include <regex>
#include <sstream>
#include <string>
#include <vector>
using namespace std;
static vector<string> files(int argc,char**argv,int s){vector<string>v;for(int i=s;i<argc;i++)v.push_back(argv[i]);return v;}
int main(int argc,char**argv){bool silent=false;string script;vector<string> fs;for(int i=1;i<argc;i++){string a=argv[i];if(a=="-n")silent=true;else if(a=="-e"&&i+1<argc)script=argv[++i];else if(a=="-f"&&i+1<argc){ifstream x(argv[++i]);stringstream b;b<<x.rdbuf();script=b.str();}else if(a.rfind("-",0)!=0&&!script.empty())fs.push_back(a);else if(a.rfind("-",0)!=0&&script.empty())script=a;}
if(script.empty()){cerr<<"chm-sed: missing script\\n";return 2;} regex sub;string repl,pat;bool global=false,hasSub=false,del=false,print=false;
if(script.size()>=3&&script[0]=='s'){char d=script[1];size_t p=script.find(d,2),q=p==string::npos?string::npos:script.find(d,p+1);if(p!=string::npos&&q!=string::npos){pat=script.substr(2,p-2);repl=script.substr(p+1,q-p-1);global=script.find('g',q)!=string::npos;sub=regex(pat);hasSub=true;}}
if(script=="d")del=true;if(script=="p")print=true;
auto process=[&](istream&in){string line;while(getline(in,line)){bool drop=del;if(hasSub)line=regex_replace(line,sub,repl,global?regex_constants::format_default:regex_constants::format_first_only);if(!drop&&!silent)cout<<line<<"\\n";if(print&&!drop)cout<<line<<"\\n";}};
if(fs.empty())process(cin);else for(auto&f:fs){ifstream in(f);if(!in){cerr<<"chm-sed: "<<f<<": open failed\\n";return 1;}process(in);}return 0;}