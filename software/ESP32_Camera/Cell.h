#ifndef CELL_H
#define CELL_H
 
struct Cell {
  int   id;
  float tempC;
  float humidity;
  float distanceCm;
  bool  ok;
};
 
extern Cell latest;
extern bool hasCell;
 
#endif
 