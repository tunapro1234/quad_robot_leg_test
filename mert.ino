#include <LiquidCrystal_I2C.h>
#include <Wire.h>
#include <Servo.h>

#define SPEED_POT_PIN A0
#define LIMIT_SWITCH_PIN 5
#define BUTTON_PIN 4
#define VICTOR_SPX_PIN 9
#define ENCODER_A_PIN 2
#define ENCODER_B_PIN 3

#define ENCODER_CPR 2400.
#define POT_MIN 10
#define POT_MAX 1000
#define HOMING_SPEED 30

#define SCREW_PITCH_MM 5.
#define SCREW_LEN_MM 50
#define GEAR_RATIO 6.


// ENCODER
volatile long enc_pos = 0L;
static const int8_t ENC_STATES [] = {0,1,-1,0,-1,0,0,1,1,0,0,-1,0,-1,1,0};  //encoder lookup table
  
/* Interrupt routine for LEFT encoder, taking care of actual counting */
ISR (PCINT2_vect){
  static uint8_t enc_last=0;
      
  enc_last <<=2; //shift previous state two places
  enc_last |= (PIND & (3 << 2)) >> 2; //read the current state into lowest 2 bits

  enc_pos += ENC_STATES[(enc_last & 0x0f)];
}

void enc_setup() {
  //set as inputs
  DDRD &= ~(1<<ENCODER_A_PIN);
  DDRD &= ~(1<<ENCODER_B_PIN);
  
  //enable pull up resistors
  PORTD |= (1<<ENCODER_A_PIN);
  PORTD |= (1<<ENCODER_B_PIN);
  
  // tell pin change mask to listen to left encoder pins
  PCMSK2 |= (1 << ENCODER_A_PIN)|(1 << ENCODER_B_PIN);
  
  // enable PCINT1 and PCINT2 interrupt in the general interrupt mask
  PCICR |= (1 << PCIE1) | (1 << PCIE2);
}

long read_encoder() {
  return enc_pos;
}

void reset_encoder() {
  enc_pos = 0;
}
// ENCODER END



// SPEED READING
unsigned long last_motor_speed_update = 0;
unsigned long motor_speed_read_interval = 10;
long last_encoder_reading = 0;
float current_rpm = 0;

void update_speed() {
  if (last_motor_speed_update == 0) {
    last_motor_speed_update = millis();
    last_encoder_reading = read_encoder();
    return;
  }

  unsigned long elapsed = millis() - last_motor_speed_update;
  if (elapsed > motor_speed_read_interval) {
      float rotation = (read_encoder() - last_encoder_reading) / ENCODER_CPR;
      current_rpm = rotation / (elapsed / 1000.) * 60.;

      // Serial.print(read_encoder());
      // Serial.print(" ");
      // Serial.print(last_encoder_reading);
      // Serial.print(" ");
      // Serial.print(rotation);
      // Serial.print(" ");
      // Serial.print(current_rpm);
      // Serial.print(" ");
      // Serial.println(elapsed/1000.);
      
      last_motor_speed_update = millis();
      last_encoder_reading = read_encoder();
  }
}

float get_rpm() {
  return current_rpm;
}

// SPEED READING END


// LCD STUFF
LiquidCrystal_I2C lcd(0x27, 20, 4);
unsigned long last_lcd_update = 0;
unsigned long lcd_update_interval = 300;

void lcd_setup() {
  lcd.init();
  lcd.backlight();

  lcd.setCursor(0, 0);
  lcd.print("Please press");
  lcd.setCursor(0, 1);
  lcd.print("the button");

  lcd.setCursor(0, 2);
  lcd.print("Speed: ");
  lcd.setCursor(0, 3);
  lcd.print(get_pot_input());
}

void lcd_update(float val1, float val2, float val3, float val4) {
  if (millis() - last_lcd_update < lcd_update_interval) {
    return;
  }
  last_lcd_update = millis();

  // lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Speed Input: ");
  lcd.print(val1, 2);
  
  lcd.setCursor(0, 1);
  lcd.print("Motor RPM: ");
  lcd.print(val2);
  
  lcd.setCursor(0, 2);
  lcd.print("Screw Pos: ");
  lcd.print(val3);
  
  lcd.setCursor(0, 3);
  lcd.print("Leg Angle: ");
  lcd.print(val4);

}
// LCD END


// VICTOR SPX
#define PWM_OFF 1500
#define PWM_MIN 1000
#define PWM_MAX 2000

Servo victor_spx;

void init_motor() {
  victor_spx.attach(VICTOR_SPX_PIN);
}

void set_motor_speed(int spd) {
  int pwm_value = map(spd, -255, 255, PWM_MIN, PWM_MAX);
  victor_spx.writeMicroseconds(pwm_value);
}
// VICTOR SPX END


// GENERAL FUNCTIONS
float get_pot_input() {
  float speed_input = map(analogRead(SPEED_POT_PIN), POT_MIN, POT_MAX, -255, 255);
  return min(255, max(-255, speed_input));
}

float is_button_pressed() {
  return !digitalRead(BUTTON_PIN);
}

float is_limit_switch_pressed() {
  return digitalRead(LIMIT_SWITCH_PIN);
}

float get_rotation() {
  return read_encoder() / ENCODER_CPR;
}

float get_output_length() {
  return get_rotation() / GEAR_RATIO * SCREW_PITCH_MM;
}

void home_system() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Homing...");
  lcd.setCursor(0, 1);
  lcd.print("Motor Speed: ");
  lcd.print(HOMING_SPEED);

  while (!is_limit_switch_pressed()) {
    // Serial.println("Waiting for limit switch");
    delay(10);
  }

  reset_encoder();
}

void setup() {
  Serial.begin(115200);
  Serial.println("Started.");
  
  pinMode(LIMIT_SWITCH_PIN, INPUT_PULLUP);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(VICTOR_SPX_PIN, OUTPUT);

  init_motor();
  lcd_setup();
  enc_setup();

  // tuş basılana kadar bekle
  while (!is_button_pressed()) {
    // Serial.println("Waiting for button!");
    lcd.setCursor(0, 3);
    lcd.print(get_pot_input());
    delay(10);
  }
  home_system();

  lcd.clear();
}

void loop() {
  float speed_input = get_pot_input();

  // motor hız ayarlaması
  if (get_output_length() >= SCREW_LEN_MM) {
    speed_input = min(0, speed_input);
  }
  if (get_output_length() <= -SCREW_LEN_MM) {
    speed_input = max(0, speed_input);
  }
  set_motor_speed(speed_input);

  lcd_update(speed_input, get_rpm(), get_output_length(), 0.);
  update_speed();
}
