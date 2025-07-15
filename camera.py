import pyrealsense2 as rs
import numpy as np

class Camera:
    def __init__(self,serial=None):
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        if serial:
            self.config.enable_device(serial)
        self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        self.pipeline.start(self.config)
        self.align_to = rs.stream.color
        self.align = rs.align(self.align_to)

        color_intrin, depth_intrin, img_color, img_depth, aligned_depth_frame, intr_coeffs, intr_matrix = self.get_aligned_images()

        self.f = [color_intrin.fx,color_intrin.fy]
        self.resolution = [color_intrin.width,color_intrin.height]

        self.K = self.get_K(fu=self.f[0],fv=self.f[1],rhou=1,rhov=1,u0=self.resolution[0]/2,v0=self.resolution[1]/2)

    def get_aligned_images(self):
        frames = self.pipeline.wait_for_frames()
        aligned_frames = self.align.process(frames)
        aligned_depth_frame = aligned_frames.get_depth_frame()
        aligned_color_frame = aligned_frames.get_color_frame()
        depth_intrin = aligned_depth_frame.profile.as_video_stream_profile().intrinsics
        color_intrin = aligned_color_frame.profile.as_video_stream_profile().intrinsics
        img_color = np.asanyarray(aligned_color_frame.get_data())
        img_depth = np.asanyarray(aligned_depth_frame.get_data())
        intr_matrix = np.array([
        [color_intrin.fx, 0, color_intrin.ppx], [0, color_intrin.fy, color_intrin.ppy], [0, 0, 1]
    ])

        return color_intrin, depth_intrin, img_color, img_depth, aligned_depth_frame, np.array(color_intrin.coeffs), intr_matrix
    
    def get_K(self,fu=0.008,fv=0.008,rhou=1e-05,rhov=1e-05,u0=250.0,v0=250.0):
        # fmt: off
        K = np.array([[fu / rhou, 0,                   u0],
                        [ 0,                  fv / rhov, v0],
                        [ 0,                  0,                    1]
                        ], dtype=np.float64)
        # fmt: on
        return K


    def stop(self):
        self.pipeline.stop()
        

    def start(self):
        self.pipeline.start(self.config)
        
    def is_opened(self):
        try:
            # Attempt to get a single frame to check if the camera is running
            frames = self.pipeline.poll_for_frames()
            return frames is not None
        except:
            return False