#include <SoftwareSerial.h>
#include <MHZ19.h>

#define BUZZER_PIN 9   // 피에조 부저 핀
#define VIBRATION_PIN 10 // 진동 모듈 핀

SoftwareSerial co2sensor(2, 3); // RX, TX
MHZ19 mhz(&co2sensor);

void setup() {
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(VIBRATION_PIN, OUTPUT);
  Serial.begin(9600); // USB 시리얼 통신 속도 설정
  co2sensor.begin(9600);

  Serial.println(F("Starting..."));
}

void loop() {
  // CO2 센서 데이터 읽기
  MHZ19_RESULT response = mhz.retrieveData();
  int co2_level = 0;

  if (response == MHZ19_RESULT_OK) {
    co2_level = mhz.getCO2(); // CO2 농도 값 가져오기
    Serial.print(F("CO2: "));
    Serial.println(co2_level);

    // CO2 농도가 2000ppm 이상이면 경보 활성화
    if (co2_level >= 2000) {
      Serial.println("⚠ CO2 농도 2000ppm 초과 → 경보 활성화");
      tone(BUZZER_PIN, 1000); // 1000Hz 주파수의 소리
      digitalWrite(VIBRATION_PIN, HIGH);
    } else {
      noTone(BUZZER_PIN);
      digitalWrite(VIBRATION_PIN, LOW);
    }
  } else {
    Serial.print(F("Error, code: "));
    Serial.println(response);
  }

  // Raspberry Pi에서 받은 경보 신호 처리
  if (Serial.available() > 0) {
    char command = Serial.read(); // Raspberry Pi에서 명령 수신

    if (command == '1') { 
      Serial.println("⚠ Raspberry Pi에서 경보 신호 수신 → 부저 및 진동 활성화");
      tone(BUZZER_PIN, 1000);
      digitalWrite(VIBRATION_PIN, HIGH);
    } else if (command == '0') {
      Serial.println("✅ Raspberry Pi에서 경보 해제 신호 수신 → 부저 및 진동 비활성화");
      noTone(BUZZER_PIN);
      digitalWrite(VIBRATION_PIN, LOW);
    }
  }

  delay(5000); // 5초 대기 후 반복
}
