import pygame
import sys
import numpy as np
import datetime
from enum import Enum
import csv
import argparse

# global settings
boundary = None
mortality_rate = None
death_time = None
susceptible_again_time = None
n_susceptible = None
n_infected = None
n_recovered = None
person_size = None
recovered_enabled = None  # SIS / SIRS switch
fast_mode = None
exposed_enabled = None # E toggle
incubation_time = None
quarantine_percentage = None 



class Color(Enum):
    GREEN = (50, 150, 50)
    RED = (255, 0, 0)
    BLUE = (0, 0, 255)
    WHITE = (255, 255, 255)
    YELLOW = (255, 255, 0) # EXPOSED


class PersonState(Enum):
    SUSCEPTIBLE = 1
    INFECTED = 2
    RECOVERED = 3
    DEAD = 4
    EXPOSED = 5


class Person(pygame.sprite.Sprite):
    def __init__(self, pos, state):
        super().__init__()

        self.image = pygame.Surface([person_size, person_size], pygame.SRCALPHA)

        self.pos = pos
        self.state = state

        self.vel = [0, 0]
        self.rect = self.image.get_rect()

        self.death_timer = death_time

        self.susceptible_again_timer = susceptible_again_time

        self.incubation_timer = incubation_time
        self.is_quarantined = False

    def update(self):
        if self.is_quarantined:
            self.vel = [0, 0]
        else:
            self.pos[0] += self.vel[0]
            self.pos[1] += self.vel[1]

            if self.pos[0] < 0:
                self.pos[0] = 0
            elif self.pos[0] > boundary[0] - person_size:
                self.pos[0] = boundary[0] - person_size

            if self.pos[1] < 0:
                self.pos[1] = 0
            elif self.pos[1] > boundary[1] - person_size:
                self.pos[1] = boundary[1] - person_size

            self.rect.x = self.pos[0]
            self.rect.y = self.pos[1]

            vel_norm = np.linalg.norm(self.vel)
            if vel_norm > 3:
                self.vel /= vel_norm
            self.vel += np.random.rand(2) * 2 - 1

        if self.state == PersonState.EXPOSED:
            self.incubation_timer -= 1
            if self.incubation_timer <= 0:
                self.state = PersonState.INFECTED
                self.death_timer = death_time
            if np.random.rand() < quarantine_percentage:
                self.is_quarantined = True
                self.vel = [0, 0]

        if self.state == PersonState.INFECTED:
            if np.random.rand() < quarantine_percentage:
                self.is_quarantined = True
                self.vel = [0, 0]
            self.death_timer -= 1
            if self.death_timer <= 0:
                if mortality_rate > np.random.rand():
                    self.state = PersonState.DEAD
                else:
                    if recovered_enabled:
                        self.state = PersonState.RECOVERED
                    else:
                        self.state = PersonState.SUSCEPTIBLE
                    self.death_timer = death_time

        if self.state == PersonState.RECOVERED:
            self.is_quarantined = False
            self.susceptible_again_timer -= 1
            if self.susceptible_again_timer <= 0:
                self.state = PersonState.SUSCEPTIBLE
                self.susceptible_again_timer = susceptible_again_time

    def render(self):
        color = Color.WHITE
        if self.state == PersonState.SUSCEPTIBLE:
            color = Color.GREEN
        elif self.state == PersonState.INFECTED:
            color = Color.RED
        elif self.state == PersonState.RECOVERED:
            color = Color.BLUE
        elif self.state == PersonState.EXPOSED:
            color = Color.YELLOW

        self.image.fill((0, 0, 0, 0))
        pygame.draw.circle(
            self.image, color.value, (10, 10), 10
        )


class Simulation:
    def __init__(self):
        self.people = []

    def spawn_random_person(self, state):
        self.people.append(Person([np.random.randint(0, boundary[0] - person_size),
                                   np.random.randint(0, boundary[1] - person_size)], state))

    def start(self):

        pygame.init()

        screen = pygame.display.set_mode(boundary)

        for _ in range(n_susceptible):
            self.spawn_random_person(PersonState.SUSCEPTIBLE)

        for _ in range(n_infected):
            self.spawn_random_person(PersonState.INFECTED)

        if recovered_enabled:
            for _ in range(n_recovered):
                self.spawn_random_person(PersonState.RECOVERED)

        clock = pygame.time.Clock()

        d = datetime.datetime.now()

        csvfile = open('simulation_stats-{date:%Y-%m-%d_%H_%M_%S}.csv'.format(date=d), 'w', newline='')
        writer = csv.writer(csvfile)
        writer.writerow(['frame', 'susceptible', 'exposed', 'infected', 'recovered', 'dead_this_frame', 'total_deaths'])

        parametersfile = open('simulation_parameters-{date:%Y-%m-%d_%H_%M_%S}.txt'.format(date=d), 'w', newline='')
        parametersfile.write("boundary " + str(boundary) +
                            "\nmortality_rate " + str(mortality_rate) +
                            "\ndeath_time " + str(death_time) +
                            "\nsusceptible_again_time " + str(susceptible_again_time) +
                            "\nn_susceptible " + str(n_susceptible) +
                            "\nn_infected " + str(n_infected) +
                            "\nn_recovered " + str(n_recovered) +
                            "\nperson_size " + str(person_size) +
                            "\nrecovered_enabled " + str(recovered_enabled) +
                            "\nfast_mode " + str(fast_mode) +
                            "\nexposed_enabled " + str(exposed_enabled) +
                            "\nincubation_time " + str(incubation_time) +
                            "\nquarantine_percentage " + str(quarantine_percentage)
                            )
        
        frame_count = 0
        total_deaths = 0
        try:
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        sys.exit()

                # Update people
                for person in self.people:
                    person.update()

                prev_count = len(self.people)
                self.people = [person for person in self.people if person.state != PersonState.DEAD]
                dead_this_frame = prev_count - len(self.people)
                total_deaths += dead_this_frame

                susceptible = 0
                exposed = 0
                infected = 0
                recovered = 0

                for person in self.people:
                    if person.state == PersonState.SUSCEPTIBLE:
                        susceptible += 1
                    elif person.state == PersonState.EXPOSED:
                        exposed += 1
                    elif person.state == PersonState.INFECTED:
                        infected += 1
                    elif person.state == PersonState.RECOVERED:
                        recovered += 1

                writer.writerow([frame_count, susceptible, exposed, infected, recovered, dead_this_frame, total_deaths])
                csvfile.flush()
                frame_count += 1

                # Check for collisions
                for person1 in self.people:
                    for person2 in self.people:
                        if pygame.sprite.collide_rect(person1, person2):
                            if person1.state == PersonState.INFECTED and person2.state == PersonState.SUSCEPTIBLE:
                                if exposed_enabled:
                                    person2.state = PersonState.EXPOSED
                                    person2.incubation_timer = incubation_time
                                else:
                                    person2.state = PersonState.INFECTED

                screen.fill(Color.WHITE.value)

                # Draw people
                for person in self.people:
                    person.render()
                    screen.blit(person.image, person.rect)

                if not fast_mode:
                    clock.tick(30)
                pygame.display.flip()
        finally:
            parametersfile.close()
            csvfile.close()
            pygame.quit()

def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "True", "true", "t", "1"):
        return True
    elif v.lower() in ("no", "False", "false", "f", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulation Configuration")

    parser.add_argument("--boundary", nargs=2, type=int, default=[600, 600], help="Simulation boundary as width height")
    parser.add_argument("--mortality_rate", type=float, default=0.5, help="Mortality rate (0.0 to 1.0)")
    parser.add_argument("--death_time", type=int, default=300, help="Time until death for infected individuals")
    parser.add_argument("--susceptible_again_time", type=int, default=300,
                        help="Time after which recovered become susceptible")
    parser.add_argument("--n_susceptible", type=int, default=40, help="Initial number of susceptible individuals")
    parser.add_argument("--n_infected", type=int, default=10, help="Initial number of infected individuals")
    parser.add_argument("--n_recovered", type=int, default=3, help="Initial number of recovered individuals")
    parser.add_argument("--person_size", type=int, default=20, help="Size of each person in the simulation")
    parser.add_argument("--recovered_enabled", type=str2bool, default=True,
                        help="Enable recovered state (True for SIRS, False for SIS)")
    parser.add_argument("--fast_mode", type=str2bool, default=True, help="Enable fast mode")
    parser.add_argument("--exposed_enabled", type=str2bool, default=False, help="Enable exposed agent state")
    parser.add_argument("--incubation_time", type=int, default=150, help="Time for exposed to preocress into infected")
    parser.add_argument("--quarantine_percentage", type=float, default=0, help="Percentage of newly infected agents (upon S->E or S->I transition) to be immediately quarantined (stop moving) (0-1).")

    args = parser.parse_args()

    boundary = args.boundary
    mortality_rate = args.mortality_rate
    death_time = args.death_time
    susceptible_again_time = args.susceptible_again_time
    n_susceptible = args.n_susceptible
    n_infected = args.n_infected
    n_recovered = args.n_recovered
    person_size = args.person_size
    recovered_enabled = args.recovered_enabled
    fast_mode = args.fast_mode
    exposed_enabled = args.exposed_enabled
    incubation_time = args.incubation_time
    quarantine_percentage = args.quarantine_percentage

    Simulation().start()
