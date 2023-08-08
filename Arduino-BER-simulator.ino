#include <MsTimer2.h>

/*
  BER-simulator

 When new serial data arrives, this sketch adds it to a String.
 When a newline is received, the loop prints the string and
 clears it.

 */

String inputString = "";         // a string to hold incoming data
boolean stringComplete = false;  // whether the string is complete

const int errPin = 13;           // the pin number of the error LED
const int tickInterval = 50;     // call timer interrupt routine every this ms
const int blinkTime = 100;       // number of ms the led is on for a blink

boolean hasVariableBER = false;   // whether the BER shall be calculated from
                                 // the analog input reading or used from the 'B' command
float targetDataRate = 5.0E9;
float targetErrorRatio = 2.1E-7;
float bitCounter = 0;
float errCounter = 0;
int counterLed1 = 0;

void setup() {
  // initialize serial
  Serial.begin(9600);
  // reserve 200 bytes for the inputString:
  inputString.reserve(200);
  // set pin modes
  pinMode(errPin, OUTPUT);
  // initialize random number generator
  randomSeed(analogRead(0));
  // start periodic timer
  MsTimer2::set(tickInterval, tick);
  MsTimer2::start();
  // initialize ber counters
}

void loop() {
  serialEvent();
  if (stringComplete) {
    parseString();
  }
}

void parseString() {
  // first character of the string determines the command
  float bc = 0;
  float ec = 0;
  int ain = 0;
  switch (inputString[0]) {
          case 'h':
        // Show help message
        Serial.println("BER simulator Available commands:");
        Serial.println("D <data rate>: Set data rate");
        Serial.println("d: Get data rate");
        Serial.println("B <BER>: Set target bit error ratio and turn variable BER off");
        Serial.println("b: Get target bit error ratio");
        Serial.println("c: Get counters: numBits,erroredBits");
        Serial.println("a: Read analog input");
        Serial.println("R: Reset counters");
        Serial.println("V: Switch to variable BER mode");
        break;
    case 'D':
      // set data rate
      targetDataRate = inputString.substring(1).toFloat();
      break;
    case 'd':
      // get data rate
      Serial.println(String(targetDataRate));
      break;
    case 'B':
      // set target bit error ratio and turn variable BER off
      hasVariableBER = false;
      targetErrorRatio = inputString.substring(1).toFloat();
      break;
    case 'b':
      // get target bit error ratio
      Serial.println(String(targetErrorRatio));
      break;
    case 'c':
      // get counters: numBits,erroredBits
      noInterrupts();
      bc = bitCounter;
      ec = errCounter;
      bitCounter = 0.0;
      errCounter = 0.0;
      interrupts();
      Serial.println(String(bc) + String(",") + String(ec));
      break;
    case 'a':
      // read analog input
      ain = analogRead(A0);
      Serial.println(String(ain));
      break;
    case 'R':
      // reset counters
      noInterrupts();
      bitCounter = 0.0;
      errCounter = 0.0;
      interrupts();
      break;
    case 'V':
      // switch to variable BER mode
      hasVariableBER = true;
      break;
    default:
      break;
  }
  // clear the string:
  inputString = "";
  stringComplete = false;
}

/*
 * called every tickInterval ms from interrupt routine
 * to do regular maintenance like updating the bit and error counters
 * and taking care of the leds
 */
void tick() {
  updateCounters();
  if (counterLed1 == 0) {
    // comparing exactly to 0 to reset the pin only once
    digitalWrite(errPin, LOW);    // turn the LED off by making the voltage LOW
  }
  if (counterLed1 >= 0) {
    // decrease counter until < 0
    counterLed1--;
  }
}

/*
 * update the bit and error counters based on current data rate and target BER
 */
void updateCounters() {
  static unsigned long lastTime;
  static float errorAccumulator;
  float expectedErrors;
  float deltaBits;
  unsigned long now = millis();
  unsigned long ellapsedMillis;
  int analogInput = analogRead(A0); // 0 .. 1023

  if (hasVariableBER) {
    targetErrorRatio = pow(10, -float(analogInput)/70.0);
  }
  ellapsedMillis = now - lastTime;
  deltaBits = float(ellapsedMillis) * targetDataRate / 1000.0;
  bitCounter += deltaBits;
  expectedErrors = deltaBits * targetErrorRatio;
  errorAccumulator += gaussianBlur(expectedErrors);
  while (errorAccumulator >= 1) {
    float errs = floor(errorAccumulator);
    errCounter += errs;
    errorAccumulator -= errs;
    blinkLed1();
  }
  lastTime = now;
}


/*
 * return a gaussian 'blurred' number of expected errors around the expected ones
 */
float gaussianBlur(float expected) {
  int ran = random(0,494);
  float scale = expected / 5.0;
  float ret = expected;
  const int gsteps[] = {4, 17, 49, 109, 197, 297, 385, 445, 477, 490, 494};
  for (int i = 0; i < 11; i++) {
    if (ran < gsteps[i]) {
      ret = expected + scale * float(i - 5);
      break;
    }
  }
  return ret;
}


void blinkLed1() {
  // blink led
  counterLed1 = blinkTime / tickInterval;
  digitalWrite(errPin, HIGH);   // turn the LED on (HIGH is the voltage level)
}


/*
  SerialEvent occurs whenever a new data comes in the
 hardware serial RX.  This routine is run between each
 time loop() runs, so using delay inside loop can delay
 response.  Multiple bytes of data may be available.
 */
void serialEvent() {
  while (Serial.available()) {
    // get the new byte:
    char inChar = (char)Serial.read();
    // add it to the inputString:
    inputString += inChar;
    // if the incoming character is a newline, set a flag
    // so the main loop can do something about it:
    if (inChar == '\n') {
      stringComplete = true;
    }
  }
}
