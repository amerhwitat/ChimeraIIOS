#include <fstream>
#include <iostream>
#include <regex>
#include <sstream>
#include <string>
#include <vector>
using namespace std;
static void run(istream&in,const string&prog,char sep){string pattern,action=prog;size_t l=prog.find('{'),r=prog.rfind('}');if(l!=string::npos&&r>l){pattern=prog.substr(0,l);action=prog.substr(l+1,r-l-1);}regex re;bool use_re=false;if(pattern.size()>2&&pattern.front()=='/'&&pattern.back()=='/'){re=regex(pattern.substr(1,pattern.size()-2));use_re=true;}string line;while(getline(in,line)){if(use_re&&!regex_search(line,re))continue;if(action.find("print")!=string::npos){size_t p=action.find('$');if(p!=string::npos&&p+1<action.size()&&isdigit((unsigned char)action[p+1])){size_t n=0;while(p+1<action.size()&&isdigit((unsigned char)action[p+1]))n=n*10+(action[++p]-'0');vector<string>f;stringstream ss(line);string x;while(getline(ss,x,sep))f.push_back(x);if(n==0)cout<<line<<"\\n";else if(n<=f.size())cout<<f[n-1]<<"\\n";}else cout<<line<<"\\n";}}}
int main(int argc,char**argv){string prog,sep=" ";vector<string>fs;for(int i=1;i<argc;i++){string a=argv[i];if(a=="-F"&&i+1<argc)sep=argv[++i][0];else if(a=="-f"&&i+1<argc){ifstream x(argv[++i]);stringstream b;b<<x.rdbuf();prog=b.str();}else if(a.rfind("-",0)!=0&&!prog.empty())fs.push_back(a);else if(a.rfind("-",0)!=0&&prog.empty())prog=a;}if(prog.empty()){cerr<<"chm-awk: missing program\\n";return 2;}if(fs.empty())run(cin,prog,sep[0]);else for(auto&f:fs){ifstream in(f);if(!in){cerr<<"chm-awk: "<<f<<": open failed\\n";return 1;}run(in,prog,sep[0]);}return 0;}