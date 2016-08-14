#include <Poofer.h>

// Poofer 0
#define p0_pin 0
#define p0_low 'a'
#define p0_High 'A'

// Poofer 1
#define p1_pin 1
#define p1_low 'b'
#define p1_High 'B'

// Poofer 2
#define p2_pin 2
#define p2_low 'c'
#define p2_High 'C'

// Poofer 3
#define p3_pin 3
#define p3_low 'd'
#define p3_High 'D'

// Poofer 4
#define p4_pin 4
#define p4_low 'e'
#define p4_High 'E'

// Poofer 5
#define p5_pin 5
#define p5_low 'f'
#define p5_High 'F'

// Poofer 6
#define p6_pin 6
#define p6_low 'g'
#define p6_High 'G'

// Poofer 7
#define p7_pin 7
#define p7_low 'h'
#define p7_High 'H'

// Poofer 8
#define p8_pin 8
#define p8_low 'i'
#define p8_High 'I'

// Poofer 9
#define p9_pin 9
#define p9_low 'j'
#define p9_High 'J'

// Poofer 10
#define p10_pin 10
#define p10_low 'k'
#define p10_High 'K'

// Poofer 11
#define p11_pin 11
#define p11_low 'l'
#define p11_high 'L'

// Poofer 12
#define p12_pin A1
#define p12_low 'm'
#define p12_High 'M'


int poofDuration = 2000;
int inByte = 0;

Poofer p0(p0_pin, poofDuration);
Poofer p1(p1_pin, poofDuration);
Poofer p2(p2_pin, poofDuration);
Poofer p3(p3_pin, poofDuration);
Poofer p4(p4_pin, poofDuration);
Poofer p5(p5_pin, poofDuration);
Poofer p6(p6_pin, poofDuration);
Poofer p7(p7_pin, poofDuration);
Poofer p8(p8_pin, poofDuration);
Poofer p9(p9_pin, poofDuration);
Poofer p10(p10_pin, poofDuration);
Poofer p11(p11_pin, poofDuration);


void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);

}

void loop() {
  if (Serial.available() > 0) {
    inByte = Serial.read();

    switch (inByte) {
      case p11_low:
        p11.low();
        break;
      case p11_high:
        p11.high();
        break;
    }
  }
  p0.updateTimer();
  p1.updateTimer();
  p2.updateTimer();
  p3.updateTimer();
  p4.updateTimer();
  p5.updateTimer();
  p6.updateTimer();
  p7.updateTimer();
  p8.updateTimer();
  p9.updateTimer();
  p10.updateTimer();
  p11.updateTimer();
}
