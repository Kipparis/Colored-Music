/* #include <Thread.h> // library for threads */

typedef unsigned int uint;

enum LedState {
    INTERPOLATING,
    IDLE
};

class Led {
public:
    Led(const int RED_PIN, const int GREEN_PIN, const int BLUE_PIN):
        r_pin(RED_PIN), g_pin(GREEN_PIN), b_pin(BLUE_PIN), state(IDLE) {
        // when led turns on, it's initially all lithen up
        // so we turn off each one of the lights
        set_red(0);     // turn off red color
        set_green(0);   // turn off green color
        set_blue(0);    // turn off blue color
        // set start point for futher instructions
        r_start = g_start = b_start = 0;
    }

    void start_interpolate(String end_point);
    void interpolate();
private:
    const int r_pin, g_pin, b_pin;
    // end point for interpolation purposes
    int r_end, g_end, b_end;
    // start point for interpolation purposes
    int r_start, g_start, b_start;
    // current state (used when interpolation breaks in the middle)
    int r_curr, g_curr, b_curr;
    // duration of interpolating (ms)
    int duration;
    // start point of interpolation
    unsigned long start_time;
    // led state (exclude spamming "analogWrite" when there're no command)
    LedState state;
    //======== Functions manipulating led color ========
    void set_red(int val) { /* analogWrite(r_pin, val); */ }
    void set_green(int val) { /* analogWrite(g_pin, val); */ }
    void set_blue(int val) { /* analogWrite(b_pin, val); */ }
    void set_rgb(int r_val, int g_val, int b_val) {
        set_red(r_val); set_green(g_val); set_blue(b_val);
    }
    //======== Interpolate asistance =========
    int interpolate_value(int start, int end, double delta) {
        return _lerp(start, end, delta);
    }
    int _lerp(int start, int end, double delta) {
        return int(start + delta * (end - start));
    }
};

// set variables so let may correctly interpolate
void Led::start_interpolate(String end_point) {
    if (state == INTERPOLATING) {
        r_start = r_curr;
        g_start = g_curr;
        b_start = b_curr;
    }

    int stop_idx = -1;
    int next_idx = end_point.indexOf(' ', stop_idx + 1);

    r_end    = end_point.substring(stop_idx + 1, next_idx).toInt();
    stop_idx     = next_idx;
    next_idx     = end_point.indexOf(' ', stop_idx + 1);

    g_end    = end_point.substring(stop_idx + 1, next_idx).toInt();
    stop_idx     = next_idx;
    next_idx     = end_point.indexOf(' ', stop_idx + 1);

    b_end    = end_point.substring(stop_idx + 1, next_idx).toInt();
    stop_idx     = next_idx;
    next_idx     = end_point.indexOf(' ', stop_idx + 1);

    duration   = end_point.substring(stop_idx + 1, next_idx).toInt();
    start_time = millis();
    Serial.print("Interpolating to\n\r");
    Serial.println(r_end);
    Serial.println(g_end);
    Serial.println(b_end);
    Serial.println(duration);

    state = INTERPOLATING;
}

void Led::interpolate() {
    if (state == INTERPOLATING) {
        unsigned long current_time = millis();
        double delta = double(current_time - start_time)/double(duration);
        // if we're done with interpolating
        if (current_time >= start_time + duration) {
            set_rgb(r_end, g_end, b_end);   // set end values
            r_start = r_end;
            g_start = g_end;
            b_start = b_end;
            state = IDLE;               // don't run this function any more
            Serial.print("Interpolated to: ");
            Serial.print(r_end);
            Serial.print(" ");
            Serial.print(g_end);
            Serial.print(" ");
            Serial.println(b_end);
        } else {
            r_curr = interpolate_value(r_start, r_end, delta);
            g_curr = interpolate_value(g_start, g_end, delta);
            b_curr = interpolate_value(b_start, b_end, delta);
            set_rgb(r_curr, g_curr, b_curr);
            Serial.print("Interpolated to: ");
            Serial.print(r_curr);
            Serial.print(" ");
            Serial.print(g_curr);
            Serial.print(" ");
            Serial.println(b_curr);
        }
    }
}

const int RED_PIN   = 18;   // red pin on led band
const int GREEN_PIN = 19;   // green pin on led band
const int BLUE_PIN  = 20;   // blue pin on led band

Led led(RED_PIN, GREEN_PIN, BLUE_PIN);

void serialEvent(); // read char every time serial is available

String inputString = "";    // string to hold incoming data
bool stringComplete = false;    // whether the string is complete

void setup() {
    // set led pins to output
    /* pinMode(RED_PIN, OUTPUT); */
    /* pinMode(GREEN_PIN, OUTPUT); */
    /* pinMode(BLUE_PIN, OUTPUT); */

    // start serial messaging
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
        led.start_interpolate(inputString);
        stringComplete = false;
        inputString = "";
    } else {
        led.interpolate();
    }
}

// led thread implementation
/* void ledBlink() { */
/*     static bool led_status = false; // led state */
/*     led_status = !led_status;       // invert state */
/*     digitalWrite(LED_PIN, led_status);  // apply led state */
/*     Serial.println("toggle light"); */
/* } */

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
