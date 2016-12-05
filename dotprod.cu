#include<stdio.h>
#include<stdlib.h>

#define SIZE 1000
#define NUM_BLOCKS 10
#define THREADS_PER_BLOCK 100

__global__ void DotProd(int *a, int *b, int *c) {
	
	__shared__ int temp[THREADS_PER_BLOCK];

	int x = threadIdx.x + blockDim.x * blockIdx.x;
	/*printf("Block ID :%d:\n", blockIdx.x);
	printf("Block Dim :%d:\n", blockDim.x);
	printf("Theard ID :%d:\n", threadIdx.x);*/
	temp[threadIdx.x] = a[x] * b[x];
	// printf("Temp:%d\n", temp[threadIdx.x]);

	__syncthreads();
	
	if (threadIdx.x == 0) 
	{
		int i,sum = 0;
		for (i = 0; i < THREADS_PER_BLOCK; i++) 
		{
			sum += temp[i];
		}
		// printf("\nSUM[%d]:%d", blockIdx.x, sum);
		atomicAdd(c, sum);
	}
}


int main() {
	int *a, *b, *c;
	int *d_a, *d_b, *d_c;
	int n = SIZE * sizeof(int);
	int i;
	
	// STEP 1 : Allocate memory for Host and Device variables
	a = (int*)malloc(n);
	b = (int*)malloc(n);
	c = (int*)malloc(sizeof(int));
	
	cudaMalloc(&d_a, n);
	cudaMalloc(&d_b, n);
	cudaMalloc(&d_c, sizeof(int));

	// STEP 2: Initialize Host variables
	*c = 0;
	for (i = 0; i < SIZE; i++) {
		a[i] = i + 1;
		b[i] = 2 * (i + 1);
	}
	
	// Display the values of the arrays
	printf("\nArray A:\n");
	for (i = 0; i < SIZE; i++) {
		printf("%d ", a[i]);
	}
	printf("\nArray B:\n");
	for (i = 0; i < SIZE; i++) {
			printf("%d ", b[i]);
	}
	printf("\n");
	// STEP 3: Copy data to device variables.
	cudaMemcpy(d_a, a, n, cudaMemcpyHostToDevice);
	cudaMemcpy(d_b, b, n, cudaMemcpyHostToDevice);
	cudaMemcpy(d_c, c, sizeof(int), cudaMemcpyHostToDevice);

	// STEP 4: Launch the Kernel
	printf("\nLaunching Kernel\n");
	DotProd <<<NUM_BLOCKS, THREADS_PER_BLOCK>>> (d_a, d_b, d_c);

	//STEP 5: Copy results from device to Host.
	cudaMemcpy(c, d_c, sizeof(int), cudaMemcpyDeviceToHost);
	
	printf("\nDot Product is: %d\n", *c);
	
	//STEP 6: Free Memory
	free(a); free(b); free(c);
	cudaFree(d_a);
	cudaFree(d_b);
	cudaFree(d_c);
	
	return 0;
}
