#include "chimera/security/biometric_auth.hpp"
namespace chimera::security {
BiometricRegistry::BiometricRegistry():methods_{
{BiometricKind::Fingerprint,"fingerprint","Fingerprint",true,false,false,true,false},
{BiometricKind::Face,"face","Face recognition",true,false,false,true,true},
{BiometricKind::Iris,"iris","Iris recognition",true,false,false,true,true},
{BiometricKind::Palm,"palm","Palm recognition",true,false,false,true,true},
{BiometricKind::HandGeometry,"hand_geometry","Hand geometry",true,false,false,true,false},
{BiometricKind::Voice,"voice","Voice recognition",true,false,false,false,true},
{BiometricKind::Vein,"vein","Palm/finger vein",true,false,false,false,true},
{BiometricKind::Fido2,"fido2","FIDO2 / passkey",true,false,false,true,false},
{BiometricKind::SmartCard,"smartcard","Smart card / PIV",true,false,false,true,false}}{}
bool BiometricRegistry::set_enabled(BiometricKind k,bool e)noexcept{for(auto&m:methods_)if(m.kind==k){m.enabled=e;return true;}return false;}
bool BiometricRegistry::set_enrolled(BiometricKind k,bool e)noexcept{for(auto&m:methods_)if(m.kind==k){m.enrolled=e;return true;}return false;}
}