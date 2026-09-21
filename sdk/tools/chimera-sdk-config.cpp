#include <iostream>
#include <string>
#include "chimera/sdk.h"
int main(int argc,char** argv){
 if(argc>1 && std::string(argv[1])=="--version"){std::cout<<chimera_sdk_version()<<"\n";return 0;}
 std::cout<<"Chimera II SDK "<<chimera_sdk_version()<<"\n";
 std::cout<<"target: "<<chimera_target_triple()<<"\n";
 std::cout<<"C/C++: gcc/g++ or clang/clang++\nC#: dotnet/Roslyn\nObjective-C: clang\nJava: javac/java\nPython: python3\n";
 return 0;
}
