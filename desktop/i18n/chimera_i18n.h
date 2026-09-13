#ifndef CHIMERA_I18N_H
#define CHIMERA_I18N_H
#ifdef __cplusplus
extern "C" {
#endif
typedef enum { CHM_LTR = 0, CHM_RTL = 1 } chm_direction_t;
typedef struct { const char *id; const char *language; const char *script; chm_direction_t direction; } chm_locale_t;
static inline chm_locale_t chm_arabic_sa(void) { return (chm_locale_t){"ar-SA", "ar", "Arabic", CHM_RTL}; }
static inline chm_locale_t chm_locale_for(const char *id) { (void)id; return chm_arabic_sa(); }
#ifdef __cplusplus
}
#endif
#endif
