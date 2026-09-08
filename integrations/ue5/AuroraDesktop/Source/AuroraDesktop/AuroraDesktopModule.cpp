#include "AuroraDesktopModule.h"
#include "Modules/ModuleManager.h"
#include "AuroraUIManager.h"

IMPLEMENT_MODULE(FAuroraDesktopModule, AuroraDesktop)

void FAuroraDesktopModule::StartupModule()
{
    // UI creation is deferred until a game viewport/world exists.
}

void FAuroraDesktopModule::ShutdownModule()
{
    FAuroraUIManager::Shutdown();
}
