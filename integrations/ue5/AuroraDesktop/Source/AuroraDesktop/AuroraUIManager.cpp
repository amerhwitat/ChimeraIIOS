#include "AuroraUIManager.h"
#include "Blueprint/UserWidget.h"
#include "Engine/World.h"

namespace { TWeakObjectPtr<UUserWidget> GPanel; }

void FAuroraUIManager::Initialize(UWorld* World)
{
    if (!World || GPanel.IsValid()) return;
    // Asset-driven by design: projects can assign their WBP_AuroraPanel class.
    // No hard-coded .uasset dependency is introduced into the plugin.
}

void FAuroraUIManager::Shutdown()
{
    if (GPanel.IsValid()) GPanel->RemoveFromParent();
    GPanel.Reset();
}
