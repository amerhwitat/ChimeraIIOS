#include "chimera/security/biometric_auth.hpp"
#include <cassert>
#include <iostream>
int main(){chimera::security::BiometricRegistry r;assert(r.methods().size()==9);assert(r.policy().allow_password_fallback);assert(r.policy().require_password_for_enrollment);assert(r.set_enabled(chimera::security::BiometricKind::Voice,true));assert(r.set_enrolled(chimera::security::BiometricKind::Fingerprint,true));std::cout<<"Aurora biometric registry: PASS\n";}