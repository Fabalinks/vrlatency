import vrlatency as vrl
import natnetclient as nn

# connect to the device
arduino = vrl.Arduino(experiment_type='Total', port='COM9', baudrate=250000)

# create a stimulation pattern
mystim = vrl.Stimulus(position=(0, 0), color=(0, 0, 0))
mystim.mesh.point_size = 5
mystim.mesh.scale.xyz = .03, .2, 1

# specify the object that is being tracked
client = nn.NatClient()
LED = client.rigid_bodies['LED']

# create an experiment app
myexp = vrl.TotalExperiment(arduino=arduino,
                            stim=mystim,
                            rigid_body=LED,
                            trials=1000,
                            screen_ind=1,
                            fullscreen=True)
myexp.run()
