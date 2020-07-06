#include <Thread.h> // library for threads

const int LED_PIN = 13; // led pin index

Thread ledThread = Thread();    // thread for led
Thread printThread = Thread();    // thread for led

void ledBlink();    // toggle led
void printOk();     // print ok in serial

void setup() {
    pinMode(LED_PIN, OUTPUT);   // set led pin in output mode

    Serial.begin(9600);

    ledThread.onRun(ledBlink);      // set task for thread
    ledThread.setInterval(1000);    // set working interval (ms)

    printThread.onRun(printOk);      // set task for thread
    printThread.setInterval(100);    // set working interval (ms)
}

void loop() {
    // is it time to run ledThread()?
    if (ledThread.shouldRun())
        ledThread.run();    // run thread
    if (printThread.shouldRun())
        printThread.run();    // run thread
}

// print ok in serial port
void printOk() {
    Serial.println("okokok\n");
}

// led thread implementation
void ledBlink() {
    static bool led_status = false; // led state
    led_status = !led_status;       // invert state
    digitalWrite(LED_PIN, led_status);  // apply led state
    Serial.write("okokok");
}
