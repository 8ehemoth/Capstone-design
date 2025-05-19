#include <SoftwareSerial.h>
#include <MHZ19.h>

#define BUZZER_PIN      9    // 피에조 부저
#define VIBRATION_PIN  10    // 진동 모듈
#define CO2_RX          2    // <- MH-Z19 TX
#define CO2_TX          3    // -> MH-Z19 RX

SoftwareSerial co2Serial(CO2_RX, CO2_TX);
MHZ19          mhz(&co2Serial);

const unsigned long CO2_PERIOD = 5000;   // 5 s
unsigned long t_prev_co2 = 0;

void setup() {
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(VIBRATION_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);
  digitalWrite(VIBRATION_PIN, LOW);

  Serial.begin(9600);       // Pi와 통신
  co2Serial.begin(9600);

  Serial.println(F("Starting..."));
}

void loop() {
  /* 1) Raspberry Pi 명령 실시간 처리 (논블로킹) */
  while (Serial.available()) {          // 버퍼에 여러 글자가 쌓일 가능성
    char cmd = Serial.read();
    if (cmd == '1') {                   // 경보 ON
      tone(BUZZER_PIN, 1000);
      digitalWrite(VIBRATION_PIN, HIGH);
      Serial.println(F("ACK:1"));       // Pi 디버깅용 응답
    } else if (cmd == '0') {            // 경보 OFF
      noTone(BUZZER_PIN);
      digitalWrite(VIBRATION_PIN, LOW);
      Serial.println(F("ACK:0"));
    }
  }

  /* 2) 5 초마다 CO₂ 측정·전송 */
  if (millis() - t_prev_co2 >= CO2_PERIOD) {
    t_prev_co2 = millis();

    if (mhz.retrieveData() == MHZ19_RESULT_OK) {
      int co2 = mhz.getCO2();
      Serial.print(F("CO2:"));
      Serial.println(co2);

      // 자체 CO₂ 경보
      if (co2 >= 2000) {
        tone(BUZZER_PIN, 1000);
        digitalWrite(VIBRATION_PIN, HIGH);
      } else {
        noTone(BUZZER_PIN);
        digitalWrite(VIBRATION_PIN, LOW);
      }
    } else {
      Serial.println(F("CO2:ERR"));
    }
  }
}
