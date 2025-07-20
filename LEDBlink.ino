const int redPin   = 13;   
bool    ledState  = false; 

void setup() {
  Serial.begin(9600);       
  pinMode(redPin, OUTPUT);  
  digitalWrite(redPin, LOW);
}

void loop() {
  if (Serial.available() > 0) {
    char c = Serial.read();     

    // if it's '1', flip the LED state
    if (c == '1') {
      ledState = !ledState;  
      digitalWrite(redPin, ledState ? HIGH : LOW);
    }
  }
}