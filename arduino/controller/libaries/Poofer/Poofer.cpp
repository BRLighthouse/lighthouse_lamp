/*
  Poofer.h - Library for handling poofers.
*/

#include "Arduino.h"
#include "Poofer.h"

Poofer::Poofer(int pin, int duration)
{
  pinMode(pin, OUTPUT);
  low();
  _pooferPin = pin;
  _duration = duration;
}

void Poofer::low()
{
  digitalWrite(_pooferPin, LOW);
}

void Poofer::high()
{
  digitalWrite(_pooferPin, HIGH);
  startTimer();
}

void Poofer::startTimer()
{
  _startTime = millis();
}

void Poofer::updateTimer()
{
  if (millis() - _startTime >= _duration) 
  {
    low();
  }
}
