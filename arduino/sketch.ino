#include <Thread.h> // library for threads

class Led {
public:
    Led(const int RED_PIN, const int GREEN_PIN, const int BLUE_PIN):
        r_pin(RED_PIN), g_pin(GREEN_PIN), b_pin(BLUE_PIN) {}
    void start_interpolate(String end_point);
    void interpolate();
private:
    const int r_pin, g_pin, b_pin;
};

// set variables so let may correctly interpolate
void Led::start_interpolate(String end_point) {

}

const int RED_PIN   = 18;   // red pin on led band
const int GREEN_PIN = 19;   // green pin on led band
const int BLUE_PIN  = 20;   // blue pin on led band

led = Led(RED_PIN, GREEN_PIN, BLUE_PIN);

void serialEvent(); // read char every time serial is available

String inputString = "";    // string to hold incoming data
bool stringComplete = false;    // whether the string is complete

void setup() {
    pinMode(LED_PIN, OUTPUT);   // set led pin in output mode

    Serial.begin(9600);

    inputString.reserve(200);   // reserve 200 bytes for the inputString
}

void loop() {
    // if there are something to read?
    if(Serial.available() > 0)
        serialEvent();
    // check if there are complete message
    if (stringComplete) {
        // tell led to set interpolation point
        led.start_interpolate(stringComplete);
        stringComplete = false;
        inputString = "";
    } else {
        led.interpolate()
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
