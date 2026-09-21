#pragma once
#include <cstddef>
#include <cstdint>
namespace chimera::shell {
enum class Dialect : uint8_t { POSIX, Bash, Zsh, Dash, Ksh, Csh, Tcsh, Fish, PowerShell, Cmd, Nushell, Elvish, Xonsh, Yash, Chimera };
struct CommandContext {
 const char* cwd;
 const char* user;
 const char* home;
 const char* path;
 uint32_t uid;
 uint32_t gid;
 bool interactive;
 bool privileged;
};
using CommandHandler=int(*)(const CommandContext&,int,const char* const*);
struct CommandSpec { const char* name; Dialect dialect; CommandHandler handler; uint32_t capabilities; };
int execute_line(const CommandContext&, Dialect, const char*, char* output, std::size_t output_size);
int run_command(const CommandContext&, const char*, int, const char* const*, char*, std::size_t);
const char* dialect_name(Dialect);
}
