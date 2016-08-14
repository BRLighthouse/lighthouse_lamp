/*
  Poofer.h - Library for handling poofers.
*/
#ifndef Poofer_h
#define Poofer_h

#include "Arduino.h"

class Poofer
{
  public:
    Poofer(int pin, int duration);
    void high();
    void low();
    void startTimer();
    void updateTimer();
  private:
    int _pooferPin;
    int _duration;
    int _startTime;
};

#endif