#import <stdio.h>

@interface ChimeraGreeter
- (void)greet;
@end

@implementation ChimeraGreeter
- (void)greet {
    puts("Hello from Objective-C on the Chimera SDK toolchain.");
}
@end

int main(void) {
    ChimeraGreeter *greeter = [ChimeraGreeter new];
    [greeter greet];
    return 0;
}
