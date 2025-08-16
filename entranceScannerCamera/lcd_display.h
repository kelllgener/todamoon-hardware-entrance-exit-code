#ifndef LCD_DISPLAY_H
#define LCD_DISPLAY_H

#include <LiquidCrystal_I2C.h>

extern LiquidCrystal_I2C lcd; // Declare the LCD object as extern

void init_lcd();
void display_message(const char *message);

#endif // LCD_DISPLAY_H
