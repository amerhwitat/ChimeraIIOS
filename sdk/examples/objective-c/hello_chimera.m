__attribute__((objc_root_class))
@interface ChimeraGreeter
+ (id)new;
- (void)greet;
@end

@implementation ChimeraGreeter
- (void)greet {
    /* AppKit/Foundation integration is supplied by a matching macOS SDK. */
}
@end

int main(void) {
    return 0;
}
