#include <Thread.h> // library for threads

const int LED_PIN = 13; // led pin index

Thread ledThread = Thread();    // thread for led

void ledBlink();    // toggle led
void serialEvent(); // read char every time serial is available

String inputString = "";    // string to hold incoming data
bool stringComplete = false;    // whether the string is complete

void setup() {
    pinMode(LED_PIN, OUTPUT);   // set led pin in output mode

    Serial.begin(9600);

    ledThread.onRun(ledBlink);      // set task for thread
    ledThread.setInterval(1000);    // set working interval (ms)

    inputString.reserve(200);   // reserve 200 bytes for the inputString
}

void loop() {
    // is it time to run ledThread()?
    if (ledThread.shouldRun())
        ledThread.run();    // run thread
    if(Serial.available() > 0)
        serialEvent();
    if (stringComplete) {
        Serial.println("STRING IS COMPLETE");
        Serial.println(inputString);
        stringComplete = false;
        inputString = "";
    }
}

// led thread implementation
void ledBlink() {
    static bool led_status = false; // led state
    led_status = !led_status;       // invert state
    digitalWrite(LED_PIN, led_status);  // apply led state
    Serial.println("toggle light");
}

/*
SerialEvent occurs whenever a new data comes in the hardware serial RX. This
routine is run between each time loop() runs, so using delay inside loop can
delay response. Multiple bytes of data may be available.
*/
void serialEvent() {
    while (Serial.available()) {
        // get the new byte:
        char inChar = (char)Serial.read();
        // add it to the inputString:
        inputString += inChar;
        // if the incoming character is a newline, set a flag so the main loop can
        // do something about it:
        if (inChar == '\n' || inChar == '\0' || inChar == '\r') {
            stringComplete = true;
        }
    }
}
