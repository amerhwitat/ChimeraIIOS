#pragma once
#include "CoreMinimal.h"

class FAuroraUIManager final
{
public:
    static void Initialize(UWorld* World);
    static void Shutdown();
};
