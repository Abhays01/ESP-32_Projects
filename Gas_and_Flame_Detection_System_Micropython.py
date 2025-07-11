import machine
import time
import json
from machine import Pin, ADC, I2C, PWM, Timer
import bluetooth
import _thread
import gc

# Enhanced Gas and Fire Detection System with Smart Features
class HazardDetectionSystem:
    def __init__(self):
        # Hardware Pin Configuration
        self.setup_pins()
        
        # Initialize components
        self.setup_lcd()
        self.setup_bluetooth()
        
        # System state variables
        self.gas_level = 0
        self.flame_detected = False
        self.system_active = True
        self.alert_active = False
        self.exhaust_running = False
        self.last_alert_time = 0
        self.alert_cooldown = 30  # seconds
        
        # Gas level thresholds (adjustable based on MQ2 calibration)
        self.GAS_SAFE = 300
        self.GAS_MEDIUM = 600
        self.GAS_DANGER = 800
        
        # Data logging for analysis
        self.data_log = []
        self.max_log_entries = 100
        
        # Status display messages
        self.status_messages = {
            'safe': 'AIR QUALITY: SAFE',
            'medium': 'GAS DETECTED: MEDIUM',
            'danger': 'DANGER: HIGH GAS!',
            'fire': 'FIRE DETECTED!!!',
            'system_ok': 'SYSTEM MONITORING'
        }
        
        print("🔥 Advanced Hazard Detection System Initialized")
        print("🌟 Features: Gas Detection, Fire Detection, Auto-Exhaust, Bluetooth Alerts")
        
    def setup_pins(self):
        """Configure all hardware pins"""
        # Sensors
        self.mq2_sensor = ADC(Pin(36))  # MQ2 gas sensor (analog)
        self.mq2_sensor.atten(ADC.ATTN_11DB)
        self.flame_sensor = Pin(39, Pin.IN, Pin.PULL_UP)  # Flame sensor (digital)
        
        # LEDs for gas level indication
        self.led_green = Pin(2, Pin.OUT)   # Safe level
        self.led_blue = Pin(4, Pin.OUT)    # Medium level
        self.led_red = Pin(5, Pin.OUT)     # Danger level
        
        # Alert systems
        self.buzzer = PWM(Pin(18), freq=2000, duty=0)  # Buzzer for alerts
        self.exhaust_fan = Pin(19, Pin.OUT)  # Exhaust fan control
        
        # System controls
        self.system_button = Pin(0, Pin.IN, Pin.PULL_UP)  # System on/off
        self.test_button = Pin(35, Pin.IN, Pin.PULL_UP)   # Test mode
        
        # Status LED
        self.status_led = PWM(Pin(25), freq=1000, duty=0)  # Breathing effect
        
    def setup_lcd(self):
        """Initialize I2C LCD display"""
        try:
            self.i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
            # Assuming PCF8574 I2C LCD backpack
            self.lcd_addr = 0x27  # Common I2C address for LCD
            self.lcd_available = True
            self.clear_lcd()
            self.write_lcd("HAZARD DETECTION", 0)
            self.write_lcd("SYSTEM STARTING..", 1)
            print("✅ LCD Display initialized")
        except Exception as e:
            print(f"⚠️  LCD initialization failed: {e}")
            self.lcd_available = False
            
    def setup_bluetooth(self):
        """Initialize Bluetooth for mobile alerts"""
        try:
            self.bt = bluetooth.BLE()
            self.bt.active(True)
            self.bt_available = True
            print("✅ Bluetooth initialized")
        except Exception as e:
            print(f"⚠️  Bluetooth initialization failed: {e}")
            self.bt_available = False
    
    def write_lcd(self, text, line):
        """Write text to LCD display"""
        if not self.lcd_available:
            return
        try:
            # Simple I2C LCD write (implement based on your LCD module)
            # This is a placeholder - implement according to your LCD library
            pass
        except Exception as e:
            print(f"LCD Error: {e}")
    
    def clear_lcd(self):
        """Clear LCD display"""
        if self.lcd_available:
            try:
                # Clear LCD implementation
                pass
            except:
                pass
    
    def read_gas_level(self):
        """Read and process MQ2 gas sensor data"""
        try:
            # Read multiple samples for stability
            samples = []
            for _ in range(10):
                samples.append(self.mq2_sensor.read())
                time.sleep_ms(10)
            
            # Calculate average and apply calibration
            raw_value = sum(samples) // len(samples)
            
            # Convert to meaningful gas level (0-1000 scale)
            # Adjust these values based on your MQ2 calibration
            self.gas_level = min(1000, max(0, (raw_value - 500) * 2))
            
            return self.gas_level
        except Exception as e:
            print(f"Gas sensor error: {e}")
            return 0
    
    def read_flame_sensor(self):
        """Read flame sensor status"""
        try:
            # Flame sensor typically gives LOW when flame detected
            self.flame_detected = not self.flame_sensor.value()
            return self.flame_detected
        except Exception as e:
            print(f"Flame sensor error: {e}")
            return False
    
    def update_gas_leds(self):
        """Update LED indicators based on gas level"""
        # Reset all LEDs
        self.led_green.off()
        self.led_blue.off()
        self.led_red.off()
        
        if self.gas_level < self.GAS_SAFE:
            self.led_green.on()  # Safe - Green
        elif self.gas_level < self.GAS_MEDIUM:
            self.led_blue.on()   # Medium - Blue
        else:
            self.led_red.on()    # Danger - Red
    
    def control_exhaust(self):
        """Smart exhaust fan control"""
        should_run = (self.gas_level >= self.GAS_MEDIUM) or self.flame_detected
        
        if should_run and not self.exhaust_running:
            self.exhaust_fan.on()
            self.exhaust_running = True
            print("🌪️  Exhaust fan started")
        elif not should_run and self.exhaust_running:
            # Keep running for 30 seconds after gas clears
            if time.time() - self.last_alert_time > 30:
                self.exhaust_fan.off()
                self.exhaust_running = False
                print("🌪️  Exhaust fan stopped")
    
    def sound_alert(self, alert_type):
        """Generate audio alerts with different patterns"""
        if alert_type == 'gas_medium':
            # Slow beep pattern
            for _ in range(3):
                self.buzzer.duty(512)
                time.sleep(0.2)
                self.buzzer.duty(0)
                time.sleep(0.3)
        elif alert_type == 'gas_danger':
            # Fast beep pattern
            for _ in range(6):
                self.buzzer.duty(512)
                time.sleep(0.1)
                self.buzzer.duty(0)
                time.sleep(0.1)
        elif alert_type == 'fire':
            # Continuous alarm
            for _ in range(20):
                self.buzzer.duty(512)
                time.sleep(0.05)
                self.buzzer.duty(0)
                time.sleep(0.05)
    
    def send_bluetooth_alert(self, message):
        """Send alert message via Bluetooth"""
        if not self.bt_available:
            return
        
        try:
            # Create alert packet
            alert_data = {
                'timestamp': time.time(),
                'type': 'HAZARD_ALERT',
                'message': message,
                'gas_level': self.gas_level,
                'flame_detected': self.flame_detected,
                'location': 'Home Safety System'
            }
            
            # Convert to JSON and send
            alert_json = json.dumps(alert_data)
            # Implement BLE characteristic write here
            print(f"📱 Bluetooth Alert: {message}")
            
        except Exception as e:
            print(f"Bluetooth error: {e}")
    
    def log_data(self):
        """Log sensor data for analysis"""
        log_entry = {
            'time': time.time(),
            'gas_level': self.gas_level,
            'flame_detected': self.flame_detected,
            'exhaust_running': self.exhaust_running
        }
        
        self.data_log.append(log_entry)
        
        # Maintain log size
        if len(self.data_log) > self.max_log_entries:
            self.data_log.pop(0)
    
    def update_display(self):
        """Update LCD display with current status"""
        if not self.lcd_available:
            return
        
        try:
            if self.flame_detected:
                self.write_lcd("🔥 FIRE DETECTED!", 0)
                self.write_lcd("EVACUATE NOW!", 1)
            elif self.gas_level >= self.GAS_DANGER:
                self.write_lcd("⚠️  HIGH GAS LEVEL", 0)
                self.write_lcd(f"Level: {self.gas_level}", 1)
            elif self.gas_level >= self.GAS_MEDIUM:
                self.write_lcd("⚠️  GAS DETECTED", 0)
                self.write_lcd(f"Level: {self.gas_level}", 1)
            else:
                self.write_lcd("✅ SYSTEM OK", 0)
                self.write_lcd(f"Air Quality: {self.gas_level}", 1)
        except Exception as e:
            print(f"Display error: {e}")
    
    def breathing_led_effect(self):
        """Create breathing effect on status LED"""
        for i in range(0, 1024, 50):
            self.status_led.duty(i)
            time.sleep_ms(50)
        for i in range(1024, 0, -50):
            self.status_led.duty(i)
            time.sleep_ms(50)
    
    def test_mode(self):
        """System test mode"""
        print("🔧 Entering test mode...")
        
        # Test all LEDs
        for led in [self.led_green, self.led_blue, self.led_red]:
            led.on()
            time.sleep(0.5)
            led.off()
        
        # Test buzzer
        self.sound_alert('gas_medium')
        
        # Test exhaust
        self.exhaust_fan.on()
        time.sleep(2)
        self.exhaust_fan.off()
        
        # Test display
        self.write_lcd("TEST MODE", 0)
        self.write_lcd("ALL SYSTEMS OK", 1)
        
        print("✅ Test mode completed")
    
    def handle_emergency(self):
        """Emergency response protocol"""
        self.alert_active = True
        self.last_alert_time = time.time()
        
        if self.flame_detected:
            self.sound_alert('fire')
            self.send_bluetooth_alert("🚨 FIRE DETECTED! Evacuate immediately!")
            # Flash red LED rapidly
            for _ in range(10):
                self.led_red.on()
                time.sleep(0.1)
                self.led_red.off()
                time.sleep(0.1)
        
        elif self.gas_level >= self.GAS_DANGER:
            self.sound_alert('gas_danger')
            self.send_bluetooth_alert(f"🚨 DANGEROUS GAS LEVEL: {self.gas_level}")
            
        elif self.gas_level >= self.GAS_MEDIUM:
            self.sound_alert('gas_medium')
            self.send_bluetooth_alert(f"⚠️ Gas detected - Level: {self.gas_level}")
    
    def run_system(self):
        """Main system loop"""
        print("🚀 Starting hazard detection system...")
        
        while self.system_active:
            try:
                # Check system button
                if not self.system_button.value():
                    print("🔴 System shutdown requested")
                    break
                
                # Check test button
                if not self.test_button.value():
                    self.test_mode()
                    time.sleep(1)  # Debounce
                
                # Read sensors
                gas_level = self.read_gas_level()
                flame_detected = self.read_flame_sensor()
                
                # Update indicators
                self.update_gas_leds()
                self.control_exhaust()
                self.update_display()
                
                # Check for emergency conditions
                current_time = time.time()
                if ((gas_level >= self.GAS_MEDIUM or flame_detected) and 
                    current_time - self.last_alert_time > self.alert_cooldown):
                    self.handle_emergency()
                
                # Log data
                self.log_data()
                
                # Status monitoring
                if gas_level < self.GAS_SAFE and not flame_detected:
                    self.alert_active = False
                
                # Memory management
                if len(self.data_log) % 20 == 0:
                    gc.collect()
                
                # System heartbeat
                print(f"💓 Gas: {gas_level}, Flame: {flame_detected}, Exhaust: {self.exhaust_running}")
                
                # Breathing LED effect (non-blocking)
                self.breathing_led_effect()
                
                time.sleep(1)  # Main loop delay
                
            except Exception as e:
                print(f"System error: {e}")
                time.sleep(5)  # Error recovery delay
    
    def shutdown(self):
        """Clean system shutdown"""
        print("🔄 Shutting down system...")
        
        # Turn off all outputs
        self.led_green.off()
        self.led_blue.off()
        self.led_red.off()
        self.buzzer.duty(0)
        self.exhaust_fan.off()
        self.status_led.duty(0)
        
        # Clear display
        self.clear_lcd()
        self.write_lcd("SYSTEM SHUTDOWN", 0)
        
        # Disable Bluetooth
        if self.bt_available:
            self.bt.active(False)
        
        print("✅ System shutdown complete")

# Enhanced initialization and startup
def main():
    """Main function with error handling"""
    print("=" * 50)
    print("🔥 ADVANCED HAZARD DETECTION SYSTEM")
    print("🌟 Features: Gas/Fire Detection, Smart Alerts")
    print("=" * 50)
    
    try:
        # Initialize system
        system = HazardDetectionSystem()
        
        # Startup sequence
        print("🔧 Running startup diagnostics...")
        time.sleep(2)
        
        # Run main system
        system.run_system()
        
    except KeyboardInterrupt:
        print("\n🛑 User interrupted")
    except Exception as e:
        print(f"💥 System error: {e}")
    finally:
        try:
            system.shutdown()
        except:
            pass
        print("🏁 Program terminated")

# Auto-start system
if __name__ == "__main__":
    main()

# Additional utility functions for advanced features
def calibrate_mq2():
    """Calibrate MQ2 sensor for accurate readings"""
    print("🔧 MQ2 Calibration Mode")
    print("Place sensor in clean air for 30 seconds...")
    
    adc = ADC(Pin(36))
    adc.atten(ADC.ATTN_11DB)
    
    samples = []
    for i in range(300):  # 30 seconds of samples
        samples.append(adc.read())
        time.sleep(0.1)
        if i % 30 == 0:
            print(f"Progress: {i//3}%")
    
    baseline = sum(samples) // len(samples)
    print(f"✅ Baseline calibrated: {baseline}")
    return baseline

def export_data_log(system):
    """Export sensor data for analysis"""
    try:
        with open('hazard_log.json', 'w') as f:
            json.dump(system.data_log, f)
        print("📊 Data exported to hazard_log.json")
    except Exception as e:
        print(f"Export error: {e}")

# Configuration settings (customize these)
CONFIG = {
    'gas_thresholds': {
        'safe': 300,
        'medium': 600,
        'danger': 800
    },
    'alert_cooldown': 30,  # seconds
    'exhaust_delay': 30,   # seconds
    'log_interval': 1,     # seconds
    'display_update': 1    # seconds
}