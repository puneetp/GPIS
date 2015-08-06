"""
Classes for sampling grasps

Author: Jeff Mahler
"""

from abc import ABCMeta, abstractmethod
import IPython
import logging
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import os
import random
import sys
import time

import scipy.stats as stats

import experiment_config as ec
import grasp
import graspable_object
from grasp import ParallelJawPtGrasp3D
import obj_file
import sdf_file

class GraspSampler:
    __metaclass__ = ABCMeta

    @abstractmethod
    def generate_grasps(self, graspable):
        """
        Create a list of candidate grasps for the object specified in graspable
        """
        pass


class GaussianGraspSampler(GraspSampler):
    def __init__(self, config):
        self._configure(config)

    def _configure(self, config):
        """Configures the grasp generator."""
        self.grasp_width = config['grasp_width']
        self.friction_coef = config['friction_coef']
        self.num_cone_faces = config['num_cone_faces']
        self.num_samples = config['grasp_samples_per_surface_point']
        self.dir_prior = config['dir_prior']
        self.alpha_thresh = 2 * np.pi / config['alpha_thresh_div']
        self.rho_thresh = config['rho_thresh']
        self.min_num_grasps = config['min_num_grasps']
        self.max_num_grasps = config['max_num_grasps']
        self.min_num_collision_free = config['min_num_collision_free_grasps']
        self.min_contact_dist = config['min_contact_dist']
        self.theta_res = 2 * np.pi * config['grasp_theta_res']
        self.alpha_inc = config['alpha_inc']
        self.rho_inc = config['rho_inc']
        self.friction_inc = config['friction_inc']

    def generate_grasps(self, graspable, sigma_scale = 2.5, target_num_grasps = None,
                        grasp_gen_mult = 3, check_collisions = False, vis = False, max_iter = 3):
        """
        Returns a list of candidate grasps for graspable object by Gaussian with
        variance specified by principal dimensions
        Params:
            graspable - (GraspableObject3D) the object to grasp
            sigma_scale - (float) the number of sigmas on the tails of the
                Gaussian for each dimension
            target_num_grasps - (int) the number of grasps to generate
            grasp_gen_mult - (float) how many times the number of target grasps
                to generate (since some will be pruned)
            max_iter - (int) max number of times generate_grasps can be called
        Returns:
            list of ParallelJawPtGrasp3D objects
        """
        # set target nums
        if target_num_grasps is None:
            target_num_grasps = self.min_num_grasps
        num_grasps_generate = grasp_gen_mult * target_num_grasps # generate 10 times too many to attempt to get enough

        # get object principal axes
        center_of_mass = graspable.mesh.center_of_mass
        principal_dims = graspable.mesh.principal_dims()
        sigma_dims = principal_dims / (2 * sigma_scale)

        # sample centers
        grasp_centers = stats.multivariate_normal.rvs(
            mean=center_of_mass, cov=sigma_dims**2, size=num_grasps_generate)

        # samples angles uniformly from sphere
        u = stats.uniform.rvs(size=num_grasps_generate)
        v = stats.uniform.rvs(size=num_grasps_generate)
        thetas = 2 * np.pi * u
        phis = np.arccos(2 * v - 1.0)
        grasp_dirs = np.array([np.sin(phis) * np.cos(thetas), np.sin(phis) * np.sin(thetas), np.cos(phis)])
        grasp_dirs = grasp_dirs.T

        # convert to grasp objects
        grasps = []
        for i in range(num_grasps_generate):
            grasp = ParallelJawPtGrasp3D(grasp_centers[i,:], grasp_dirs[i,:], self.grasp_width)
            contacts_found, contacts = grasp.close_fingers(graspable)

            # add grasp if it has valid contacts
            if contacts_found and np.linalg.norm(contacts[0].point - contacts[1].point) > self.min_contact_dist:
                grasps.append(grasp)


        # visualize
        if vis:
            for grasp in grasps:
                plt.clf()
                h = plt.gcf()
                plt.ion()
                grasp.close_fingers(graspable, vis=vis)
                plt.show(block=False)
                time.sleep(0.5)

            grasp_centers_grid = graspable.sdf.transform_pt_obj_to_grid(grasp_centers.T)
            grasp_centers_grid = grasp_centers_grid.T
            com_grid = graspable.sdf.transform_pt_obj_to_grid(center_of_mass)

            plt.clf()
            ax = plt.gca(projection = '3d')
            graspable.sdf.scatter()
            ax.scatter(grasp_centers_grid[:,0], grasp_centers_grid[:,1], grasp_centers_grid[:,2], s=60, c=u'm')
            ax.scatter(com_grid[0], com_grid[1], com_grid[2], s=120, c=u'y')
            ax.set_xlim3d(0, graspable.sdf.dims_[0])
            ax.set_ylim3d(0, graspable.sdf.dims_[1])
            ax.set_zlim3d(0, graspable.sdf.dims_[2])
            plt.show()

        # optionally use openrave to check collisionsx
        if check_collisions:
            rave.raveSetDebugLevel(rave.DebugLevel.Error)
            grasp_checker = pgc.OpenRaveGraspChecker(view=vis)

            # loop through grasps
            collision_free_grasps = []
            for grasp in grasps:
                rotated_grasps = grasp.transform(graspable.tf, self.theta_res)
                rotated_grasps = grasp_checker.prune_grasps_in_collision(graspable, rotated_grasps, auto_step=True, delay=0.0)
                if len(rotated_grasps) > 0:
                    collision_free_grasps.append(grasp)

            grasps = collision_free_grasps

        # return the number requested
        k = 1
        while len(grasps) < target_num_grasps and k < max_iter:
            logging.info('Iteration %d of Gaussian sampling only found %d/%d grasps, trying again.',
                         k-1, len(grasps), target_num_grasps)
            additional_grasps = self.generate_grasps(
                graspable, sigma_scale, target_num_grasps - len(grasps), grasp_gen_mult * 2,
                check_collisions, vis, max_iter=1)
            grasps = grasps + additional_grasps
            k = k+1

        random.shuffle(grasps)
        if len(grasps) > target_num_grasps:
            logging.info('Iteration %d of Gaussian sampling found %d random grasps, truncating to %d.',
                         k, len(grasps), target_num_grasps)
            grasps = grasps[:target_num_grasps]
        else:
            logging.info('Iteration %d of Gaussian sampling found %d random grasps.',
                         k, len(grasps))
        return grasps

def test_gaussian_grasp_sampling(vis=False):
    np.random.seed(100)

    h = plt.figure()
    ax = h.add_subplot(111, projection = '3d')

    sdf_3d_file_name = 'data/test/sdf/Co.sdf'
    sf = sdf_file.SdfFile(sdf_3d_file_name)
    sdf_3d = sf.read()

    mesh_name = 'data/test/meshes/Co.obj'
    of = obj_file.ObjFile(mesh_name)
    m = of.read()

    graspable = graspable_object.GraspableObject3D(sdf_3d, mesh=m, model_name=mesh_name)

    config_file = 'cfg/correlated.yaml'
    config = ec.ExperimentConfig(config_file)
    sampler = GaussianGraspSampler(config)

    start_time = time.clock()
    grasps = sampler.generate_grasps(graspable, target_num_grasps=200, vis=False)
    end_time = time.clock()
    duration = end_time - start_time
    logging.info('Found %d random grasps' %(len(grasps)))
    logging.info('Gaussian grasp candidate generation took %f sec' %(duration))

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    test_gaussian_grasp_sampling()
