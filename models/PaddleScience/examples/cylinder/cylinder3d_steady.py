"""
cylinder3d_steady ce test
"""

import paddlescience as psci
import numpy as np
import paddle

paddle.seed(1)
np.random.seed(1)

paddle.enable_static()
# paddle.disable_static()

# load real data
real_data = np.load("flow_steady/re20_5.0.npy").astype("float32")
real_cord = real_data[:, 0:3]
real_sol = real_data[:, 3:7]

cc = (0.0, 0.0)
cr = 0.5
geo = psci.geometry.CylinderInCube(origin=(-8, -8, -0.5), extent=(25, 8, 0.5), circle_center=cc, circle_radius=cr)

geo.add_boundary(name="left", criteria=lambda x, y, z: abs(x + 8.0) < 1e-4)
geo.add_boundary(name="right", criteria=lambda x, y, z: abs(x - 25.0) < 1e-4)
geo.add_boundary(name="circle", criteria=lambda x, y, z: ((x - cc[0]) ** 2 + (y - cc[1]) ** 2 - cr ** 2) < 1e-4)

# discretize geometry
geo_disc = geo.discretize(npoints=60000, method="sampling")
geo_disc.user = real_cord

# N-S
pde = psci.pde.NavierStokes(nu=0.05, rho=1.0, dim=3, time_dependent=False, weight=[4.0, 0.01, 0.01, 0.01])

# boundary condition on left side: u=1, v=w=0
bc_left_u = psci.bc.Dirichlet("u", rhs=1.0)
bc_left_v = psci.bc.Dirichlet("v", rhs=0.0)
bc_left_w = psci.bc.Dirichlet("w", rhs=0.0)

# boundary condition on right side: p=0
bc_right_p = psci.bc.Dirichlet("p", rhs=0.0)

# boundary on circle
bc_circle_u = psci.bc.Dirichlet("u", rhs=0.0)
bc_circle_v = psci.bc.Dirichlet("v", rhs=0.0)
bc_circle_w = psci.bc.Dirichlet("w", rhs=0.0)

# add bounday and boundary condition
pde.add_bc("left", bc_left_u, bc_left_v, bc_left_w)
pde.add_bc("right", bc_right_p)
pde.add_bc("circle", bc_circle_u, bc_circle_v, bc_circle_w)

# discritize pde
pde_disc = pde.discretize(geo_disc=geo_disc)

# network
net = psci.network.FCNet(num_ins=3, num_outs=4, num_layers=10, hidden_size=50, activation="tanh")

# loss
loss = psci.loss.L2(p=2)

# Algorithm
algo = psci.algorithm.PINNs(net=net, loss=loss)

# Optimizer
opt = psci.optimizer.Adam(learning_rate=0.001, parameters=net.parameters())

# Solver
solver = psci.solver.Solver(pde=pde, algo=algo, opt=opt)

solver.feed_data_user(real_sol)  # add real solution

solution = solver.solve(num_epoch=10)

# TODO 5. label physic_info
psci.visu.save_vtk(geo_disc=pde.geometry, data=solution)

# psci.visu.__save_vtk_raw(cordinate=real_cord, data=real_sol)
