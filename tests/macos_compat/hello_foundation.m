#import <Foundation/Foundation.h>

int main(void) {
    @autoreleasepool {
        NSString *platform = @"portable GNUstep/Foundation build";
        NSLog(@"MACOS_COMPAT_SMOKE_OK: %@", platform);
    }
    return 0;
}
