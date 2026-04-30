#!/usr/bin/env python3
"""
Encoder Test Düğümü

Bu düğüm:
1. /wheel_ticks konusunu dinleyerek 3 motorun encoder verilerini konsola loglar.
2. Açık çevrim (open-loop) olarak /cmd_vel yayını yapar:
   - 1 metre ileri gider (0.2 m/s ile 5 saniye)
   - Kısa bir süre duraklar
   - 1 metre geri gider (-0.2 m/s ile 5 saniye)
3. İşlem tamamlanınca durur.
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Int32MultiArray

class EncoderTestNode(Node):
    def __init__(self):
        super().__init__('encoder_test_node')
        
        # Encoder verilerini okumak için abonelik
        self.ticks_sub = self.create_subscription(
            Int32MultiArray,
            '/wheel_ticks',
            self.ticks_callback,
            10
        )
        
        # Hız komutları göndermek için yayıncı
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # Test senaryosu durum değişkenleri
        self.state = 'FORWARD'
        self.start_time = self.get_clock().now()
        
        # 20 Hz kontrol döngüsü
        self.timer = self.create_timer(0.05, self.control_loop)
        
        self.get_logger().info('='*50)
        self.get_logger().info('Encoder Test Düğümü Başlatıldı.')
        self.get_logger().info('Görev: 1m İleri -> Dur -> 1m Geri.')
        self.get_logger().info('='*50)
        self.get_logger().info('1 metre ileri gidiliyor...')

    def ticks_callback(self, msg: Int32MultiArray):
        """Encoder verileri geldiğinde konsola loglar."""
        ticks = msg.data
        if len(ticks) >= 3:
            # ticks sıralaması: [t1(Sağ-Ön), t2(Sol-Ön), t3(Arka)] (roboclaw_driver_node'a göre)
            self.get_logger().info(
                f'[ENCODER] T1(Sağ-Ön): {ticks[0]} | T2(Sol-Ön): {ticks[1]} | T3(Arka): {ticks[2]}'
            )

    def control_loop(self):
        """Hareket senaryosunu işleten döngü."""
        elapsed_time = (self.get_clock().now() - self.start_time).nanoseconds / 1e9
        cmd = Twist()
        
        if self.state == 'FORWARD':
            # 0.2 m/s hızla 5 saniye ileri git -> 1 metre (açık çevrim)
            if elapsed_time <= 5.0:
                cmd.linear.x = 0.2
            else:
                cmd.linear.x = 0.0
                self.state = 'PAUSE'
                self.start_time = self.get_clock().now()
                self.get_logger().info('Hedefe varıldı. Duraklanıyor...')
                
        elif self.state == 'PAUSE':
            # 2 saniye bekle
            if elapsed_time > 2.0:
                self.state = 'BACKWARD'
                self.start_time = self.get_clock().now()
                self.get_logger().info('1 metre geri gidiliyor...')
                
        elif self.state == 'BACKWARD':
            # -0.2 m/s hızla 5 saniye geri git -> 1 metre
            if elapsed_time <= 5.0:
                cmd.linear.x = -0.2
            else:
                cmd.linear.x = 0.0
                self.state = 'DONE'
                self.get_logger().info('Test tamamlandı. Motorlar durduruldu.')
                
        elif self.state == 'DONE':
            cmd.linear.x = 0.0
            cmd.linear.y = 0.0
            cmd.angular.z = 0.0
            self.cmd_pub.publish(cmd)
            # Uygulamayı düzgün bir şekilde sonlandır
            raise SystemExit

        self.cmd_pub.publish(cmd)

def main(args=None):
    rclpy.init(args=args)
    node = EncoderTestNode()
    try:
        rclpy.spin(node)
    except SystemExit:
        pass
    except KeyboardInterrupt:
        pass
    finally:
        # Çıkarken robotu güvenli durdur
        stop_cmd = Twist()
        node.cmd_pub.publish(stop_cmd)
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
