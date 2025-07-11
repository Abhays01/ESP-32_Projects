#include <BluetoothSerial.h>

BluetoothSerial SerialBT;

char receivedChar;
const int MR1 = 12; 
const int MR2 = 14; 
const int ML1 = 27;
const int ML2 = 26;

void setup() {
  Serial.begin(115200);
  SerialBT.begin("AbhayBOT");
  pinMode(MR1, OUTPUT); 
  pinMode(MR2, OUTPUT);
  pinMode(ML1, OUTPUT);
  pinMode(ML2, OUTPUT);
}

void Forward(){
       
      digitalWrite(MR1,HIGH);
      digitalWrite(MR2,LOW); 
      digitalWrite(ML1,LOW);
      digitalWrite(ML2,HIGH);
}
void Backward(){
      digitalWrite(MR1,LOW);
      digitalWrite(MR2,HIGH);
      digitalWrite(ML1,HIGH);
      digitalWrite(ML2,LOW);
}
void Left(){
      digitalWrite(MR1,HIGH);
      digitalWrite(MR2,LOW);
      digitalWrite(ML1,HIGH);
      digitalWrite(ML2,LOW);
}
void Right(){
      digitalWrite(MR1,LOW);
      digitalWrite(MR2,HIGH);
      digitalWrite(ML1,LOW);
      digitalWrite(ML2,HIGH);
}
void Stop(){
      digitalWrite(MR1,LOW); 
      digitalWrite(MR2,LOW);
      digitalWrite(ML1,LOW); 
      digitalWrite(ML2,LOW); 
}
void loop() {
    receivedChar =(char)SerialBT.read();

  if (Serial.available()) {
    digitalWrite(25,HIGH);
        digitalWrite(33,HIGH);
    SerialBT.write(Serial.read());
  
  }
  if (SerialBT.available()) {
     
    Serial.print ("Received:");
    Serial.println(receivedChar); 
    
    if(receivedChar == 'F')
    {
      Forward();
       
    }
    if(receivedChar == 'B')
    {
 
      Backward(); 
    }         
     if(receivedChar == 'L')
    {

      Left();
    }        
    if(receivedChar == 'R')
    {

      Right(); 
    }
    if(receivedChar == 'S')
    {
      Stop();
    }
  }
  delay(20);
}