// oled_display.h
#ifndef OLED_DISPLAY_H
#define OLED_DISPLAY_H

#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

extern Adafruit_SSD1306 display; // Declare the display object as extern

void init_oled();
void display_message(const char *message);

#endif // OLED_DISPLAY_H
